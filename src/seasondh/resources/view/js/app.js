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
        $scope.options.tab['tab5_val'] = 'debug';
        $scope.options.infotab = 1;
        $scope.options.sidemenu = true;
        $timeout()
    }

    var _cache = cache_builder('datahub.app.editor.' + dataset_id + '.' + app_id);
    $scope.options = _cache.get();
    if (!$scope.options) option_builder();
    $scope.$watch('options', function () {
        _cache.update($scope.options);
    }, true);

    if ($scope.options.sidemenu === null) $scope.options.sidemenu = true;

    $scope.status_drag = '';

    $scope.event = {};

    var dragbasewidth = 0;
    var dragbaseheight = 0;
    var vh50 = window.innerHeight / 2;

    $scope.event.drag = {
        onstart: function (self) {
            $scope.status_drag = 'unselectable';
            $timeout();

            vh50 = window.innerHeight / 2;

            var target = $(self.element).attr('target');
            dragbasewidth = $('.' + target).width();

            var tds = $('.code-top td.bg-white');
            for (var i = 0; i < tds.length; i++) {
                var w = $(tds[i]).width();
                if (i == tds.length - 1) {
                    $(tds[i]).width('auto');
                } else {
                    $(tds[i]).width(w);
                }
            }

            var tds = $('.code-tabs-top td');
            for (var i = 0; i < tds.length; i++) {
                var w = $(tds[i]).width();
                if (i == tds.length - 1) {
                    $(tds[i]).width('auto');
                } else {
                    $(tds[i]).width(w);
                }
            }

            if ($scope.options.layout < 5) return;
            dragbaseheight = $('.tab-5').height();
        },
        onmove: function (self, pos) {
            var target = $(self.element).attr('target');

            if (target == 'tab-5') {
                var move_y = pos.y;
                var resize_h = dragbaseheight - move_y - 1;
                var base_h = vh50 - 65;
                var diff = base_h - resize_h;
                var hstr = 'calc(100vh - 130px - ' + resize_h + 'px)';
                $('.code-top td').height(hstr);
                hstr = 'calc(100vh - 132px - ' + resize_h + 'px)';
                $('.code-top td .code-input').height(hstr);
                $('.code-top td .code-input .CodeMirror').height(hstr);

                $('.code-bottom td').height(resize_h);
                $('.code-bottom td .code-input').height(resize_h);
                $('.code-bottom td .code-input .CodeMirror').height(resize_h);

                return;
            }

            var move_x = pos.x;

            if (dragbasewidth + move_x - 1 < 400) return;
            if (move_x > 0 && $('.code-top td.bg-white:last-child').width() < 400) {
                return;
            }

            $('.' + target).width(dragbasewidth + move_x - 1);
        },
        onend: function (self) {
            $scope.status_drag = '';
            $timeout();
        }
    };

    $timeout(function () {
        if ($scope.options.layout > 4) {
            var resize_h = 300;
            var hstr = 'calc(100vh - 130px - ' + resize_h + 'px)';
            $('.code-top td').height(hstr);
            hstr = 'calc(100vh - 132px - ' + resize_h + 'px)';
            $('.code-top td .code-input').height(hstr);
            $('.code-top td .code-input .CodeMirror').height(hstr);

            $('.code-bottom td').height(resize_h);
            $('.code-bottom td .code-input').height(resize_h);
            $('.code-bottom td .code-input .CodeMirror').height(resize_h);
        }
    })

    $scope.$watch('options.tab', function () {
        try {
            var hstr = $('.code-top td')[0].style.height;
            $timeout(function () {
                $('.h-half .code-top td .code-input').height(hstr);
                $('.h-half .code-top td .code-input .CodeMirror').height(hstr);
            });
        } catch (e) {
        }
    }, true);

    $scope.event.toggle = {};
    $scope.event.toggle.sidemenu = function () {
        $scope.options.sidemenu = !$scope.options.sidemenu;
        $timeout();
    }

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

    $scope.serverlogs = [];

    $scope.event.clear_log = function () {
        $scope.serverlogs = [];
        $timeout();
    }

    var logger = function (code, msg) {
        $scope.serverlogs.push(msg);
        $timeout(function () {
            setTimeout(function () {
                $('#serverlog-debug').scrollTop(10000000);
            }, 100);
        });
    }

    $scope.event.iframe = function (findurl) {
        var url = "/api/iframe/" + dataset_id + "/" + app_id + '?' + new Date().getTime();
        if (findurl) {
            return url;
        }
        $timeout(function () {
            $('iframe').attr('src', url);
            var iframes = $('iframe');
            for (var i = 0; i < iframes.length; i++) {
                $(iframes[i]).one('load', function () {
                    this.contentWindow.API.logger = logger;
                    for (var j = 0; j < this.contentWindow.API.logger_cache.length; j++) {
                        logger(this.contentWindow.API.logger_cache[j][0], this.contentWindow.API.logger_cache[j][1]);
                    }
                    this.contentWindow.API.logger_cache = [];
                });
            }
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