/**
 * This is the view for the user account (profile) page.
 */
girder.views.UserAccountView = girder.View.extend({
    events: {
        'submit #g-password-change-form': function (event) {
            event.preventDefault();
            this.$('.g-validation-failed-message').empty();

            if (this.$('#g-password-new').val() !==
                this.$('#g-password-retype').val()) {
                this.$('.g-validation-failed-message').text(
                    'Passwords do not match, try again.');
                this.$('#g-password-retype,#g-password-new').val('');
                this.$('#g-password-new').focus();
                return;
            }

            this.user.off('g:error').on('g:error', function (err) {
                var msg = err.responseJSON.message;
                this.$('.g-validation-failed-message').text(msg);
            }, this).off('g:passwordChanged')
                    .on('g:passwordChanged', function () {
                girder.events.trigger('g:alert', {
                    icon: 'ok',
                    text: 'Password changed.',
                    type: 'success',
                    timeout: 4000
                });
                this.$('#g-password-old,#g-password-new,#g-password-retype').val('');
            }, this).changePassword(
                this.$('#g-password-old').val(),
                this.$('#g-password-new').val());
        }
    },

    initialize: function (settings) {
        this.tab = settings.tab || 'info';
        this.user = settings.user || girder.currentUser;
        this.isCurrentUser = girder.currentUser &&
            settings.user.get('_id') === girder.currentUser.get('_id');

        if (!this.user) {
            console.error('Not logged in.');
            girder.events.trigger('g:navigateTo', girder.views.UsersView);
        }
        this.render();
    },

    render: function () {
        this.$el.html(jade.templates.userSettings({
            user: this.user,
            girder: girder
        }));

        girder.router.navigate('useraccount/' + this.user.get('_id') +
                               '/' + this.tab);

        _.each($('.g-account-tabs>li>a'), function (el) {
            var tabLink = $(el);
            var view = this;
            tabLink.tab().on('shown.bs.tab', function (e) {
                view.tab = $(e.currentTarget).attr('name');
                girder.router.navigate('useraccount/' +
                    view.user.get('_id') + '/' + view.tab);
            });

            if (tabLink.attr('name') === this.tab) {
                tabLink.tab('show');
            }
        }, this);

        return this;
    }
});

girder.router.route('useraccount/:id/:tab', 'accountTab', function (id, tab) {
    var user = new girder.models.UserModel();
    user.set({
        _id: id
    }).on('g:fetched', function () {
        girder.events.trigger('g:navigateTo', girder.views.UserAccountView, {
            user: user,
            tab: tab
        });
    }, this).on('g:error', function () {
        girder.events.trigger('g:navigateTo', girder.views.UsersView);
    }, this).fetch();
});
