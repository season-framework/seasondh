var content_controller = function ($scope, $timeout, $sce) {
    _builder($scope, $timeout);
    $scope.trustAsHtml = $sce.trustAsHtml;

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

    var option_builder = function () {
        $scope.options = {};
        $scope.options.layout = 2;
        $scope.options.tab = {};
        $scope.options.tab['tab1_val'] = 'html';
        $scope.options.tab['tab2_val'] = 'preview';
        $scope.options.infotab = 1;
        $timeout()
    }

    var _cache = cache_builder('datahub.app.editor.' + dataset_id + '.' + app_id);
    $scope.options = _cache.get();
    if (!$scope.options) option_builder();
    $scope.$watch('options', function () {
        _cache.update($scope.options);
    }, true);

    $scope.event = {};
    $scope.event.info = function () {
        $.post('/api/dataset/info/' + dataset_id, function (res) {
            $scope.dataset_info = res.data;
            try {
                if ($scope.dataset_info.dataloader.id == app_id) {
                    $scope.info = $scope.dataset_info.dataloader;
                }
            } catch (e) {
            }

            try {
                for (var i = 0; i < $scope.dataset_info.apps.length; i++) {
                    if ($scope.dataset_info.apps[i].id == app_id) {
                        $scope.info = $scope.dataset_info.apps[i];
                    }
                }
            } catch (e) {
            }

            $timeout();
        });
    }

    $scope.event.iframe = function (findurl) {
        var url = "/api/iframe/" + dataset_id + "/" + app_id + '?' + new Date().getTime();
        if (findurl) {
            return url;
        }
        $timeout(function () {
            $('iframe').attr('src', url);
        });
    };

    $scope.event.create_tag = function (tag) {
        if ($scope.info.tags.indexOf(tag) >= 0 || !tag || tag.length == 0) {
            return;
        }

        $scope.info.tags.push(tag);
        $scope.tag_input = "";
        $timeout();
    }

    $scope.event.save = function (cb) {
        var data = angular.copy($scope.dataset_info);

        $.post('/api/update/' + dataset_id, { data: JSON.stringify(data) }, function (res) {
            $scope.event.iframe();
            if (cb) return cb(res);
            if (res.code == 200) {
                return toastr.success('저장되었습니다');
            }
            toastr.error('오류가 발생하였습니다.');
        });
    }

    $scope.event.select_file = function () {
        $('#import-file').click();
    }

    var fileinput = document.getElementById('import-file');
    fileinput.addEventListener("change", async event => {
        const json = JSON.parse(await fileinput.files[0].text());
        if (json.mode != $scope.info.mode) return;

        $scope.info.title = json.title;
        $scope.info.about = json.about;
        $scope.info.tags = json.tags;
        $scope.info.view = json.view;
        $scope.info.code = json.code;

        $scope.event.save();
    });

    // init page
    $scope.event.iframe();
    $scope.event.info();

    shortcutjs(window, {
        'control s': function (ev) {
            ev.preventDefault();
            $scope.event.save();
        },
        'default': function (ev, name) {
        }
    });
};