#!/usr/bin/env python
# -*- coding: utf-8 -*- 

#
# Copyright 2018 Guenter Bartsch
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
# 
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

#
# seq2seq model that translates wiktionary hyphenated word + IPA into our IPA style
#
# code based on https://github.com/keras-team/keras/blob/master/examples/lstm_seq2seq.py
#

import os
import sys
import string
import codecs
import json
import logging

from keras.models import Model
from keras.layers import Input, LSTM, Dense
import numpy as np

from nltools            import misc
from speech_lexicon     import Lexicon

BATCH_SIZE      = 64   # Batch size for training.
MODELDIR        = 'data/dst/speech/de/wiktionary_models'

class WiktionarySeq2Seq(object):

    def __init__ (self, name):

        self.modeldir = '%s/%s' % (MODELDIR, name)
        if not os.path.exists(self.modeldir):
            misc.mkdirs(self.modeldir)

        self.metafn    = '%s/meta.json'    % self.modeldir
        self.weightsfn = '%s/weights.json' % self.modeldir

    def _setup_model (self):

        num_encoder_tokens      = len(self.input_token_index)
        num_decoder_tokens      = len(self.target_token_index)

        # Define an input sequence and process it.
        encoder_inputs = Input(shape=(None, num_encoder_tokens))
        encoder = LSTM(self.latent_dim, return_state=True)
        encoder_outputs, state_h, state_c = encoder(encoder_inputs)
        # We discard `encoder_outputs` and only keep the states.
        encoder_states = [state_h, state_c]

        # Set up the decoder, using `encoder_states` as initial state.
        decoder_inputs = Input(shape=(None, num_decoder_tokens))
        # We set up our decoder to return full output sequences,
        # and to return internal states as well. We don't use the
        # return states in the training model, but we will use them in inference.
        decoder_lstm = LSTM(self.latent_dim, return_sequences=True, return_state=True)
        decoder_outputs, _, _ = decoder_lstm(decoder_inputs,
                                             initial_state=encoder_states)
        decoder_dense = Dense(num_decoder_tokens, activation='softmax')
        decoder_outputs = decoder_dense(decoder_outputs)

        # Define the model that will turn
        # `encoder_input_data` & `decoder_input_data` into `decoder_target_data`
        self.model = Model([encoder_inputs, decoder_inputs], decoder_outputs)

        # Next: inference mode (sampling).
        # Here's the drill:
        # 1) encode input and retrieve initial decoder state
        # 2) run one step of decoder with this initial state
        # and a "start of sequence" token as target.
        # Output will be the next target token
        # 3) Repeat with the current target token and current states

        # Define sampling models
        self.encoder_model = Model(encoder_inputs, encoder_states)

        decoder_state_input_h = Input(shape=(self.latent_dim,))
        decoder_state_input_c = Input(shape=(self.latent_dim,))
        decoder_states_inputs = [decoder_state_input_h, decoder_state_input_c]
        decoder_outputs, state_h, state_c = decoder_lstm( decoder_inputs, initial_state=decoder_states_inputs)
        decoder_states = [state_h, state_c]
        decoder_outputs = decoder_dense(decoder_outputs)
        self.decoder_model = Model( [decoder_inputs] + decoder_states_inputs, [decoder_outputs] + decoder_states)

    def _encode_data (self, input_texts, target_texts):

        num_encoder_tokens      = len(self.input_token_index)
        num_decoder_tokens      = len(self.target_token_index)

        # one-hot encoding of the data

        encoder_input_data  = np.zeros( (len(input_texts), self.max_encoder_seq_length, num_encoder_tokens), dtype='float32')
        decoder_input_data  = np.zeros( (len(input_texts), self.max_decoder_seq_length, num_decoder_tokens), dtype='float32')
        decoder_target_data = np.zeros( (len(input_texts), self.max_decoder_seq_length, num_decoder_tokens), dtype='float32')

        for i, (input_text, target_text) in enumerate(zip(input_texts, target_texts)):
            for t, char in enumerate(input_text):
                encoder_input_data[i, t, self.input_token_index[char]] = 1.
            for t, char in enumerate(target_text):
                # decoder_target_data is ahead of decoder_input_data by one timestep
                decoder_input_data[i, t, self.target_token_index[char]] = 1.
                if t > 0:
                    # decoder_target_data will be ahead by one timestep
                    # and will not include the start character.
                    decoder_target_data[i, t - 1, self.target_token_index[char]] = 1.

        return encoder_input_data, decoder_input_data, decoder_target_data

    def load (self):

        with open(self.metafn, 'r') as metaf:
            js = metaf.read()
            meta = json.loads(js)

        self.input_token_index       = meta['input_token_index'     ]
        self.target_token_index      = meta['target_token_index'    ]
        self.max_encoder_seq_length  = meta['max_encoder_seq_length']
        self.max_decoder_seq_length  = meta['max_decoder_seq_length']
        self.latent_dim              = meta['latent_dim'            ]

        logging.info('latent_dim                     : %d' % self.latent_dim)
        logging.info('Max sequence length for inputs : %d' % self.max_encoder_seq_length)
        logging.info('Max sequence length for outputs: %d' % self.max_decoder_seq_length)

        # Reverse-lookup token index to decode sequences back to something readable.
        self.reverse_input_char_index  = dict( (i, char) for char, i in self.input_token_index.items())
        self.reverse_target_char_index = dict( (i, char) for char, i in self.target_token_index.items())

        self._setup_model()

        self.model.load_weights(self.weightsfn)

    def _interleave_input_text(self, word, ipa):
        
        res = u""
        
        l = len(word) if len(word) > len(ipa) else len(ipa)
        for i in range(l):
            if i<len(word):
                res += word[i]
            if i<len(ipa):
                res += ipa[i]
        
        return res

    def train (self, words, ipas, target_texts_, epochs=100, latent_dim=256, max_encoder_seq_length=0, max_decoder_seq_length=0, val_split=0.2):

        self.latent_dim = 256

        #
        # compute char dicts and other meta data
        #

        input_characters  = set()
        target_characters = set()
        input_texts       = []
        target_texts      = []

        for word, ipa, target_text in zip(words, ipas, target_texts_):

            input_text = self._interleave_input_text(word, ipa)
            input_texts.append(input_text)

            # We use "tab" as the "start sequence" character
            # for the targets, and "\n" as "end sequence" character.
            target_text = '\t' + target_text + '\n'
            target_texts.append(target_text)

            for char in input_text:
                if char not in input_characters:
                    input_characters.add(char)
            for char in target_text:
                if char not in target_characters:
                    target_characters.add(char)

        self.max_encoder_seq_length = max_encoder_seq_length if max_encoder_seq_length else max([len(txt) for txt in input_texts])
        self.max_decoder_seq_length = max_decoder_seq_length if max_decoder_seq_length else max([len(txt) for txt in target_texts])

        input_characters        = sorted(list(input_characters))
        target_characters       = sorted(list(target_characters))

        self.input_token_index  = dict( [(char, i) for i, char in enumerate(input_characters)])
        self.target_token_index = dict( [(char, i) for i, char in enumerate(target_characters)])

        # Reverse-lookup token index to decode sequences back to something readable.
        self.reverse_input_char_index  = dict( (i, char) for char, i in self.input_token_index.items())
        self.reverse_target_char_index = dict( (i, char) for char, i in self.target_token_index.items())

        num_encoder_tokens      = len(self.input_token_index)
        num_decoder_tokens      = len(self.target_token_index)

        logging.info('Number of samples              : %d' % len(input_texts))
        logging.info('Number of unique input tokens  : %d' % num_encoder_tokens)
        logging.info('Number of unique output tokens : %d' % num_decoder_tokens)
        logging.info('Max sequence length for inputs : %d' % self.max_encoder_seq_length)
        logging.info('Max sequence length for outputs: %d' % self.max_decoder_seq_length)

        meta = { 'input_token_index'      : self.input_token_index,
                 'target_token_index'     : self.target_token_index,
                 'max_encoder_seq_length' : self.max_encoder_seq_length,
                 'max_decoder_seq_length' : self.max_decoder_seq_length,
                 'latent_dim'             : self.latent_dim }

        with open(self.metafn, 'w') as metaf:
            metaf.write(json.dumps(meta)) 
        
        logging.info('%s written.' % self.metafn)

        #
        # train/validation split
        #

        train_input_texts  = []
        train_target_texts = []
        val_input_texts    = []
        val_target_texts   = []
        
        for input_text, target_text in zip(input_texts, target_texts):
            if len(train_input_texts) * val_split > len(val_input_texts):
                val_input_texts.append(input_text)
                val_target_texts.append(target_text)
            else:
                train_input_texts.append(input_text)
                train_target_texts.append(target_text)

        logging.info("%d samples will be used for training, %d for validation." % (len(train_input_texts), len(val_input_texts)))

        train_encoder_input_data, train_decoder_input_data, train_decoder_target_data = self._encode_data(train_input_texts, train_target_texts)
        val_encoder_input_data,   val_decoder_input_data,   val_decoder_target_data   = self._encode_data(val_input_texts,   val_target_texts)

        #
        # setup model, train
        #

        self._setup_model()

        self.model.compile(optimizer='rmsprop', loss='categorical_crossentropy')

        best_val_loss = 100000.0

        for epoch in range(epochs):

            hist = self.model.fit([train_encoder_input_data, train_decoder_input_data], train_decoder_target_data,
                                  batch_size=BATCH_SIZE,
                                  #epochs=EPOCHS,
                                  epochs=1,
                                  validation_data = ([val_encoder_input_data, val_decoder_input_data], val_decoder_target_data))

            # print hist.history, repr(hist.history)

            # {'loss': [0.7145306808321943], 'val_loss': [0.6716832236252952]}

            val_loss = hist.history['val_loss'][0]

            logging.info("EPOCH %4d/%4d: val_loss=%s, best_val_loss=%s" % (epoch+1, epochs, repr(val_loss), repr(best_val_loss)))

            if val_loss < best_val_loss:
                # Save model
                self.model.save_weights(self.weightsfn)

                logging.info("EPOCH %4d/%4d: NEW BEST VAL LOSS => %s written." % (epoch+1, epochs, self.weightsfn))
                best_val_loss = val_loss

    def predict(self, word, ipa):

        input_text          = self._interleave_input_text(word, ipa)

        # print input_text

        num_encoder_tokens  = len(self.input_token_index)
        num_decoder_tokens  = len(self.target_token_index)

        # one-hot encoding of the data

        input_seq  = np.zeros( (1, self.max_encoder_seq_length, num_encoder_tokens), dtype='float32')

        for t, char in enumerate(input_text):
            input_seq[0, t, self.input_token_index[char]] = 1.
            # print char, input_seq[0, t]

        # Encode the input as state vectors.
        states_value = self.encoder_model.predict(input_seq)

        # Generate empty target sequence of length 1.
        target_seq = np.zeros((1, 1, num_decoder_tokens))
        # Populate the first character of target sequence with the start character.
        target_seq[0, 0, self.target_token_index['\t']] = 1.

        # Sampling loop for a batch of sequences
        # (to simplify, here we assume a batch of size 1).
        stop_condition = False
        decoded_sentence = ''
        while not stop_condition:
            output_tokens, h, c = self.decoder_model.predict( [target_seq] + states_value)

            # Sample a token
            sampled_token_index = np.argmax(output_tokens[0, -1, :])
            sampled_char = self.reverse_target_char_index[sampled_token_index]
            decoded_sentence += sampled_char

            # Exit condition: either hit max length
            # or find stop character.
            if (sampled_char == '\n' or len(decoded_sentence) > self.max_decoder_seq_length):
                stop_condition = True

            # Update the target sequence (of length 1).
            target_seq = np.zeros((1, 1, num_decoder_tokens))
            target_seq[0, 0, sampled_token_index] = 1.

            # Update states
            states_value = [h, c]

        return decoded_sentence


