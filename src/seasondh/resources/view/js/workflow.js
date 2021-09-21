var content_controller = function ($scope, $timeout) {
    $scope.event = {};
    $scope.iframe = {};
    $scope.data = {};

    function makeid(length) {
        var result = '';
        var characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
        var charactersLength = characters.length;
        for (var i = 0; i < length; i++) {
            result += characters.charAt(Math.floor(Math.random() *
                charactersLength));
        }
        return result;
    }

    $scope.event.delete = function () {
        if (!$scope.allow_delete) {
            $scope.allow_delete = true;
            $timeout();
            return;
        }

        location.href = "/api/delete/" + workflow_id;
    }

    $scope.event.info = function () {
        $.post('/api/workflow/info/' + workflow_id, function (res) {
            $scope.info = res.data;

            $timeout(function () {
                $scope.iframe.load_all();
            });
        });
    }

    $scope.event.fullscreen = function (app) {
        $scope.data.dataprocess_app = app;
        var url = "/api/iframe/" + $scope.info.id + "/" + app.id;
        $('#dataprocess-iframe').attr('src', url);
        $('#modal-dataprocess').modal('show');
    }

    $scope.event.reload = function (app) {
        $scope.iframe.loader(app);
    }

    $scope.event.add = function () {
        $scope.info.apps.push({
            title: "New App",
            about: "",
            tags: [],
            batch_api: "",
            view_api: "",
            html: "",
            js: "",
            css: ""
        });

        $timeout();
    }

    $scope.event.save = function (cb) {
        var data = angular.copy($scope.info);
        $.post('/api/update/' + workflow_id, { data: JSON.stringify(data) }, function (res) {
            if (cb) return cb(res);
            if (res.code == 200) {
                location.reload();
                return;
            }
            toastr.error('오류가 발생하였습니다.');
        });
    }

    $scope.iframe.load_all = function (cb) {
        try {
            var _loader = function (index, cb) {
                if (!index) index = 0;
                if (!$scope.info.apps[index]) {
                    if (cb) cb();
                    return;
                }

                var app = $scope.info.apps[index];
                $scope.iframe.loader(app, function () {
                    _loader(index + 1, cb);
                });
            }

            _loader();
        } catch (e) {
        }
    }

    $scope.iframe.loader = function (app, cb) {
        if (!app || !app.id) return;
        $timeout(function () {
            var url = "/api/iframe/" + $scope.info.id + "/" + app.id;
            $('#iframe-' + app.id).unbind();
            $('#iframe-' + app.id).on('load', function () {
                iframeheight = this.contentWindow.document.body.offsetHeight;
                $(this).parent().height(iframeheight + 'px');

                var _this = this;

                var _height_changed_detect = function () {
                    try {
                        iframeheight = _this.contentWindow.document.body.offsetHeight;
                        var parent_height = $(_this).parent().height();
                        if (parent_height != iframeheight) $(_this).parent().height(iframeheight + 'px');
                    } catch (e) {
                    }

                    setTimeout(_height_changed_detect, 1000);
                }

                _height_changed_detect();
                if (cb) cb();
            });
            $('#iframe-' + app.id).attr('src', url);
        });
    }

    $scope.event.click = {};

    $scope.event.click.trash = function (app) {
        $scope.selected = app;
        $('#modal-delete').modal('show');
        $timeout();
    }

    $scope.event.click.delete = function (app) {
        $scope.info.apps.remove(app);
        $scope.event.save(function () {
            location.reload();
        });
        $timeout();
    }

    $scope.event.click.item = function (app) {
        $scope.event.save(function () {
            location.href = '/app/' + workflow_id + '/' + app.id;
        });
    }

    $scope.event.move_up = function (idx, arr) {
        if (idx === 0) return;
        arr.splice(idx - 1, 0, arr.splice(idx, 1)[0]);
        $timeout();
        $scope.iframe.load_all();
    }

    $scope.event.move_down = function (idx, arr) {
        if (idx === arr.length - 1) return;
        arr.splice(idx + 1, 0, arr.splice(idx, 1)[0]);
        $timeout();
        $scope.iframe.load_all();
    }


    $scope.event.import = function () {
        $('#import-file').click();
    }

    var fileinput = document.getElementById('import-file');
    fileinput.addEventListener("change", async event => {
        const json = JSON.parse(await fileinput.files[0].text());
        json.id = $scope.info.id;
        $scope.info = json;
        $scope.event.save(function () {
            location.reload();
        });
    });

    $scope.event.info();
};