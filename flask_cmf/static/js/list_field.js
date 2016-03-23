(function($){
    function _FieldList(container) {
        this.$container = $(container);
        this.template = this.$container.find('.cmf-list-form-item-template').val();
        this.$fieldsContainer = this.$container.find('.cmf-list-fields-container');
        this.$addBtn = this.$container.find('.cmf-list-form-add-btn').on('click', function(self){
            return function() {
                self.onAdd();
            }
        }(this));

        this.$container.on('click', '.cmf-list-form-remove-btn', function() {
            $(this).parents('.cmf-list-form-item').remove();
        });

        this.createFromTemplate = function(index) {
            return this.template.replace(/\*/g, index)
        };

        this.items = function() {
            return this.$container.find('.cmf-list-form-item');
        };

        this.onAdd = function() {
            var items = this.items(),
                index = items.length,
                html = this.createFromTemplate(index);
            this.$fieldsContainer.append($(html));
        }
    }


    $(function(){
        $(".cmf-list-form-container").each(function(){
            new _FieldList(this);
        })
    });
})(jQuery);
