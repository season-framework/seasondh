var content_controller = function ($scope, $timeout) {
    $scope.event = {};
    $scope.event.login = function (password) {
        $.post('/api/auth/login', { password: password }).always(function (res) {
            if (res.code == 200)
                return location.reload();
            toastr.error('Password Mismatched');
        })
    }
};