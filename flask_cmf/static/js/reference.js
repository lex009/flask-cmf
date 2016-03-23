(function($, global){
    function ReferenceModal($link) {
        this.$link = $link;
        this.$container = $link.parent().parent();
        this.html =
            '<div class="modal">' +
                '<div class="modal-dialog cmf-reference-dialog">' +
                    '<div class="modal-content">' +
                        '<div class="modal-header">' +
                            '<button type="button" class="close" data-dismiss="modal" aria-label="Close"><span aria-hidden="true">×</span></button>' +
                            'Choose reference' +
                        '</div>' +
                        '<div class="modal-body">' +
                        '<iframe frameborder="0" allowtransparency="true" class="modal-body" src="/reference-admin/ref-basecontent/"></iframe>'
                        '</div>' +
                    '</div>' +
                '</div>' +
            '</div>';

        this.show = function() {
            var $modal = $(this.html),
                that = this;
            $('body').append($modal);
            $modal.find('iframe').on('choose', function(e, data) {
                that.$container.find(".cmf-reference-id").val(data.id);
                that.$container.find(".cmf-reference-classname").val(data.classname);

                $.get(data.url, function(data) {
                    console.log(that.$container.find('.cmf-reference-label'));
                    that.$container.find('.cmf-reference-label').html('<a href="' + data['url'] + '">' + data['label'] + '</a>');
                });

                $modal.modal('hide').remove();

                that.$container.find('.cmf-reference-clear-link').removeClass('hidden');
                that.$link.addClass('hidden');
            });
            $modal.modal();
        };
    }

    $(function() {
        $(document).on('click', '.cmf-reference-link', function(e) {
            e.preventDefault();
            var m = new ReferenceModal($(this));
            m.show();
        });

        $(document).on('click', '.cmf-reference-clear-link', function(e) {
            e.preventDefault();
            var parent = $(this).parent().parent();
            parent.find('.cmf-reference-id').val('');
            parent.find('.cmf-reference-classname').val('');
            parent.find('.cmf-reference-label').empty();
            parent.find('.cmf-reference-link').removeClass('hidden');
            $(this).addClass('hidden');
        });
    });
})(jQuery, window);
