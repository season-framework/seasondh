toastr.options = {
    "closeButton": false,
    "debug": false,
    "newestOnTop": false,
    "progressBar": false,
    "positionClass": "toast-bottom-right",
    "preventDuplicates": false,
    "onclick": null,
    "showDuration": 300,
    "hideDuration": 1000,
    "timeOut": 5000,
    "extendedTimeOut": 1000,
    "showEasing": "swing",
    "hideEasing": "linear",
    "showMethod": "fadeIn",
    "hideMethod": "fadeOut"
};

; (function (global, factory) {
    typeof exports === 'object' && typeof module !== 'undefined'
        && typeof require === 'function' ? factory(require('../moment')) :
        typeof define === 'function' && define.amd ? define(['../moment'], factory) :
            factory(global.moment)
}(this, (function (moment) {
    'use strict';

    //! moment.js locale configuration

    var ko = moment.updateLocale('ko', {
        months: '1월_2월_3월_4월_5월_6월_7월_8월_9월_10월_11월_12월'.split('_'),
        monthsShort: '1월_2월_3월_4월_5월_6월_7월_8월_9월_10월_11월_12월'.split(
            '_'
        ),
        weekdays: '일요일_월요일_화요일_수요일_목요일_금요일_토요일'.split('_'),
        weekdaysShort: '일_월_화_수_목_금_토'.split('_'),
        weekdaysMin: '일_월_화_수_목_금_토'.split('_'),
        longDateFormat: {
            LT: 'A h:mm',
            LTS: 'A h:mm:ss',
            L: 'YYYY.MM.DD.',
            LL: 'YYYY년 MMMM D일',
            LLL: 'YYYY년 MMMM D일 A h:mm',
            LLLL: 'YYYY년 MMMM D일 dddd A h:mm',
            l: 'YYYY.MM.DD.',
            ll: 'YYYY년 MMMM D일',
            lll: 'YYYY년 MMMM D일 A h:mm',
            llll: 'YYYY년 MMMM D일 dddd A h:mm',
        },
        calendar: {
            sameDay: '오늘 LT',
            nextDay: '내일 LT',
            nextWeek: 'dddd LT',
            lastDay: '어제 LT',
            lastWeek: '지난주 dddd LT',
            sameElse: 'L',
        },
        relativeTime: {
            future: '%s 후',
            past: '%s 전',
            s: '몇 초',
            ss: '%d초',
            m: '1분',
            mm: '%d분',
            h: '한 시간',
            hh: '%d시간',
            d: '하루',
            dd: '%d일',
            M: '한 달',
            MM: '%d달',
            y: '일 년',
            yy: '%d년',
        },
        dayOfMonthOrdinalParse: /\d{1,2}(일|월|주)/,
        ordinal: function (number, period) {
            switch (period) {
                case 'd':
                case 'D':
                case 'DDD':
                    return number + '일';
                case 'M':
                    return number + '월';
                case 'w':
                case 'W':
                    return number + '주';
                default:
                    return number;
            }
        },
        meridiemParse: /AM|PM/,
        isPM: function (token) {
            return token === 'PM';
        },
        meridiem: function (hour, minute, isUpper) {
            return hour < 12 ? 'AM' : 'PM';
        },
    });

    return ko;
})));

Number.prototype.format = function () {
    if (this == 0) return 0;
    var reg = /(^[+-]?\d+)(\d{3})/;
    var n = (this + '');
    while (reg.test(n)) n = n.replace(reg, '$1' + ',' + '$2');
    return n;
};

String.prototype.number_format = function () {
    var num = parseFloat(this);
    if (isNaN(num)) return "0";

    return num.format();
};

Array.prototype.remove = function () {
    var what, a = arguments, L = a.length, ax;
    while (L && this.length) {
        what = a[--L];
        while ((ax = this.indexOf(what)) !== -1) {
            this.splice(ax, 1);
        }
    }
    return this;
};

String.prototype.string = function (len) { var s = '', i = 0; while (i++ < len) { s += this; } return s; };
String.prototype.zf = function (len) { return "0".string(len - this.length) + this; };
Number.prototype.zf = function (len) { return this.toString().zf(len); };

Date.prototype.format = function (f) {
    if (!this.valueOf()) return " ";

    var weekName = ["일요일", "월요일", "화요일", "수요일", "목요일", "금요일", "토요일"];
    var d = this;

    return f.replace(/(yyyy|yy|MM|dd|E|hh|mm|ss|a\/p)/gi, function ($1) {
        switch ($1) {
            case "yyyy": return d.getFullYear();
            case "yy": return (d.getFullYear() % 1000).zf(2);
            case "MM": return (d.getMonth() + 1).zf(2);
            case "dd": return d.getDate().zf(2);
            case "E": return weekName[d.getDay()];
            case "HH": return d.getHours().zf(2);
            case "hh": return ((h = d.getHours() % 12) ? h : 12).zf(2);
            case "mm": return d.getMinutes().zf(2);
            case "ss": return d.getSeconds().zf(2);
            case "a/p": return d.getHours() < 12 ? "AM" : "PM";
            default: return $1;
        }
    });
};

var calc_working_time = function (st, et) {
    if (!st) return 0;

    var today = moment().format('YYYY-MM-DD');
    var tday = moment(st).format('YYYY-MM-DD');

    var lst = new Date(moment(st).format('YYYY-MM-DD 12:00:00')).getTime(); // 점심시간
    var wet = new Date(moment(st).format('YYYY-MM-DD 22:00:00')).getTime(); // 업무종료시간

    st = st.getTime();

    if (et) {
        et = et.getTime();
    } else if (today == tday) {
        et = new Date().getTime();
    } else {
        et = wet;
    }

    if (et > wet) et = wet;

    var minus = 0;
    if (st <= lst) {
        minus = (et - lst) / 1000 / 60 / 60;
        if (minus > 1) {
            minus = 1;
        }
    }
    if (minus < 0) minus = 0;

    var t = Math.round(((et - st) / 1000 / 60 / 60 - minus) * 100) / 100;
    return t;
}

var get_tinymce_opt = function (id, readonly) {
    var TINYMCE_OPT = {
        selector: 'textarea#' + id,
        plugins: 'print preview paste searchreplace autolink directionality code visualblocks visualchars fullscreen image link media template codesample table charmap hr pagebreak nonbreaking anchor toc insertdatetime advlist lists wordcount imagetools textpattern noneditable help charmap quickbars emoticons',
        menubar: false,

        toolbar: 'undo redo | styleselect | h2 h3 h4 | bold italic underline strikethrough | fontselect fontsizeselect formatselect | alignleft aligncenter alignright alignjustify | outdent indent |  numlist bullist | forecolor backcolor removeformat | hr pagebreak | charmap emoticons | preview print | image media link codesample | ltr rtl | code',
        toolbar_sticky: true,

        image_advtab: true,
        importcss_append: true,
        image_title: true,
        image_caption: true,
        automatic_uploads: true,
        file_picker_types: 'image',
        file_picker_callback: function (cb, value, meta) {
            var input = document.createElement('input');
            input.setAttribute('type', 'file');
            input.setAttribute('accept', 'image/*');

            input.onchange = function () {
                var file = this.files[0];

                var reader = new FileReader();
                reader.onload = function () {
                    var id = 'blobid' + (new Date()).getTime();
                    var blobCache = tinymce.activeEditor.editorUpload.blobCache;
                    var base64 = reader.result.split(',')[1];
                    var blobInfo = blobCache.create(id, file, base64);
                    blobCache.add(blobInfo);
                    cb(blobInfo.blobUri(), { title: file.name });
                };
                reader.readAsDataURL(file);
            };

            input.click();
        },

        codesample_languages: [
            { text: 'Bash', value: 'bash' },
            { text: 'HTML/XML', value: 'markup' },
            { text: 'JavaScript', value: 'javascript' },
            { text: 'CSS', value: 'css' },

            { text: 'Apache Conf', value: 'apacheconf' },
            { text: 'PHP', value: 'php' },
            { text: 'Python', value: 'python' },

            { text: 'SQL', value: 'sql' },

            { text: 'Java', value: 'java' },
            { text: 'C', value: 'c' },
            { text: 'C#', value: 'csharp' },
            { text: 'C++', value: 'cpp' },
            { text: 'Ruby', value: 'ruby' },
        ],

        height: '100%',

        quickbars_selection_toolbar: 'styleselect | bold italic | quicklink h2 h3 blockquote quickimage quicktable',
        noneditable_noneditable_class: 'mceNonEditable',
        toolbar_mode: 'wrap',

        contextmenu: 'link image imagetools table',
        skin: 'oxide',
        content_css: '/resources/theme/libs/fontawesome/css/all.min.css,/resources/theme/libs/tabler/dist/css/tabler.min.css,/resources/theme/libs/tabler/dist/css/tabler-flags.min.css,/resources/theme/libs/tabler/dist/css/tabler-payments.min.css,/resources/theme/libs/tabler/dist/css/tabler-buttons.min.css,/resources/theme/libs/tabler/dist/css/demo.min.css,/resources/theme/libs/highlight/default.min.css,/resources/theme/less/theme.less',
        content_style: 'body { background: white; max-width: 1024px; padding: 32px;} ul {margin: 0;}',
        readonly: readonly
    }

    return TINYMCE_OPT;
};