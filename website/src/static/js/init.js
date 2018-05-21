(function($){
  $(function(){

    $('.button-collapse').sideNav();
    if (!sessionStorage.alreadyClicked) {
    	$('.tap-target').tapTarget('open');
        sessionStorage.alreadyClicked = 1;
    }

  }); // end of document ready
})(jQuery); // end of jQuery name space