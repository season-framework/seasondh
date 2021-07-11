var content_controller = function ($scope, $timeout) {
    $scope.event = {};
    $scope.data = {};

    $scope.event.list = function () {
        $.post('/api/dataset/list', function (res) {
            $scope.data.list = res.data;
            console.log($scope.data.list);

            $timeout();
        });
    }

    $scope.event.click = function(id) {
        location.href = "/dataset/" + id;
    }

    $scope.event.list();
};