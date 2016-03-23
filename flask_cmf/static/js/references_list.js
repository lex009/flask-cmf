(function($){
    $(function(){
        $(".cmf-reference-choose").on("click", function(e){
            window.parent.$(window.frameElement).trigger('choose', $(this).data());
        });
    });
})(jQuery);
