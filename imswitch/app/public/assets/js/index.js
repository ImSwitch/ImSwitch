define("env", ["require", "exports"], function (require, exports) {
    "use strict";
    Object.defineProperty(exports, "__esModule", { value: true });
    exports.env = void 0;
    exports.env = {
        streaming_port: 8000,
        streaming_uri: '/RecordingController/video_feeder',
        alternative_base_uri: 'localhost'
    };
});
define("service/http.service", ["require", "exports", "env"], function (require, exports, env_1) {
    "use strict";
    Object.defineProperty(exports, "__esModule", { value: true });
    exports.HttpService = void 0;
    class HttpService {
        get(uri) {
            return new Promise((resolve, reject) => {
                var _a;
                const base_uri = (_a = env_1.env.alternative_base_uri) !== null && _a !== void 0 ? _a : '';
                const xhr = new XMLHttpRequest();
                xhr.open('GET', base_uri + uri, true);
                xhr.onload = () => {
                    if (xhr.status >= 200 && xhr.status < 300) {
                        resolve(xhr.response);
                    }
                    else {
                        reject({
                            status: xhr.status,
                            message: xhr.statusText
                        });
                    }
                };
                xhr.onerror = () => {
                    reject({
                        status: xhr.status,
                        message: xhr.statusText
                    });
                };
                xhr.send();
            });
        }
    }
    exports.HttpService = HttpService;
});
define("service/camera.service", ["require", "exports"], function (require, exports) {
    "use strict";
    Object.defineProperty(exports, "__esModule", { value: true });
    exports.CameraService = void 0;
    class CameraService {
        constructor(httpService) {
            this.httpService = httpService;
        }
        setAngle(horizontalAngle, verticalAngle) {
            return this.httpService.get(`/servo?hor=${horizontalAngle}&ver=${verticalAngle}`);
        }
        setFlashlight(on) {
            return this.httpService.get(`/flash?value=${on ? 1 : 0}`);
        }
    }
    exports.CameraService = CameraService;
});
define("handler/camera.handler", ["require", "exports"], function (require, exports) {
    "use strict";
    Object.defineProperty(exports, "__esModule", { value: true });
    exports.CameraHandler = void 0;
    class CameraHandler {
        constructor(cameraService, rangeHorizontal, rangeVertical, checkFlashlight, checkInvHor, checkInvVer) {
            var _a, _b;
            this.cameraService = cameraService;
            this.rangeHorizontal = rangeHorizontal;
            this.rangeVertical = rangeVertical;
            this.checkFlashlight = checkFlashlight;
            this.checkInvHor = checkInvHor;
            this.checkInvVer = checkInvVer;
            this.rangeHorizontal.addEventListener('change', (event) => this.horizontalChange());
            this.rangeVertical.addEventListener('change', (event) => this.verticalChange());
            this.checkFlashlight.addEventListener('change', (event) => this.flashlightChange());
            this.horizontalHint = (_a = this.rangeHorizontal.nextSibling) === null || _a === void 0 ? void 0 : _a.nextSibling;
            this.verticalHint = (_b = this.rangeVertical.nextSibling) === null || _b === void 0 ? void 0 : _b.nextSibling;
        }
        flashlightChange() {
            this.cameraService.setFlashlight(this.checkFlashlight.checked);
        }
        horizontalChange() {
            this.horizontalHint.innerHTML = this.rangeHorizontal.value + '&deg;';
            this.updateAngles();
        }
        verticalChange() {
            this.verticalHint.innerHTML = this.rangeVertical.value + '&deg;';
            this.updateAngles();
        }
        updateAngles() {
            let hor = parseInt(this.rangeHorizontal.value);
            let ver = parseInt(this.rangeVertical.value);
            if (this.checkInvHor.checked)
                hor = -hor;
            if (this.checkInvVer.checked)
                ver = -ver;
            this.cameraService
                .setAngle(hor + 90, ver + 90)
                .then(response => console.log(response), error => console.error(error));
        }
    }
    exports.CameraHandler = CameraHandler;
});
define("service/configuration.service", ["require", "exports"], function (require, exports) {
    "use strict";
    Object.defineProperty(exports, "__esModule", { value: true });
    exports.ConfigurationService = void 0;
    class ConfigurationService {
        constructor(httpService) {
            this.httpService = httpService;
        }
        configureStreaming(param, value) {
            return this.httpService.get(`/control?var=${param}&val=${value}`);
        }
    }
    exports.ConfigurationService = ConfigurationService;
});
define("handler/streaming.handler", ["require", "exports", "env"], function (require, exports, env_2) {
    "use strict";
    Object.defineProperty(exports, "__esModule", { value: true });
    exports.StreamingHandler = void 0;
    class StreamingHandler {
        constructor(viewport, waitingElement) {
            this.viewport = viewport;
            this.waitingElement = waitingElement;
            this.viewport.style.display = 'none';
            this.waitingElement.style.display = 'block';
            this.viewport.addEventListener('error', () => {
                console.log('Streaming error');
                this.viewport.style.display = 'none';
                this.waitingElement.style.display = 'block';
            });
            this.setupVideoStreaming();
        }
        setupVideoStreaming() {
            console.log('Location origin: ' + location.origin);
            const streamingUrl = (env_2.env.alternative_base_uri || location.origin) + ':' + env_2.env.streaming_port + env_2.env.streaming_uri;
            this.viewport.src = streamingUrl;
            this.viewport.style.display = 'block';
            this.waitingElement.style.display = 'none';
            console.log('Streaming url: ' + streamingUrl);
        }
    }
    exports.StreamingHandler = StreamingHandler;
});
define("handler/configuration.handler", ["require", "exports", "env"], function (require, exports, env_3) {
    "use strict";
    Object.defineProperty(exports, "__esModule", { value: true });
    exports.ConfigurationHandler = void 0;
    class ConfigurationHandler {
        constructor(txtIpAddress, cmbFrameSize, configurationService, streamingHandler) {
            this.txtIpAddress = txtIpAddress;
            this.cmbFrameSize = cmbFrameSize;
            this.configurationService = configurationService;
            this.streamingHandler = streamingHandler;
            txtIpAddress.addEventListener('change', (event) => this.setAlternativeIp());
            cmbFrameSize.addEventListener('change', (event) => this.setFrameSize());
        }
        setAlternativeIp() {
            const value = this.txtIpAddress.value;
            if (value && /\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/.test(value)) {
                env_3.env.alternative_base_uri = 'http://' + value;
            }
            else {
                env_3.env.alternative_base_uri = '';
            }
            this.streamingHandler.setupVideoStreaming();
        }
        setFrameSize() {
            const value = this.cmbFrameSize.value;
            this.configurationService.configureStreaming('framesize', value).then(response => console.log(response), error => console.error(error));
        }
    }
    exports.ConfigurationHandler = ConfigurationHandler;
});
define("service/navigation.service", ["require", "exports"], function (require, exports) {
    "use strict";
    Object.defineProperty(exports, "__esModule", { value: true });
    exports.NavigationService = void 0;
    class NavigationService {
        constructor(httpService) {
            this.httpService = httpService;
        }
        stop() {
            return this.httpService.get('/stop');
        }
        setSpeed(leftForward, pwmLeft, rightForward, pwmRight) {
            let axis = "X";
            let dist = 0;
            if (leftForward) {
                axis = "X";
                dist = pwmLeft;
            }
            else if (rightForward) {
                axis = "Y";
                dist = pwmRight;
            }
            else {
                axis = "XY";
                dist = pwmLeft;
            }
            return this.httpService.get(`:8000/PositionerController/movePositioner?positionerName=ESP32Stage&axis=${axis}&dist=${dist}&isAbsolute=false`);
            return this.httpService.get(`/navi?dl=${leftForward ? 1 : 0}&sl=${pwmLeft}&dr=${rightForward ? 1 : 0}&sr=${pwmRight}`);
        }
    }
    exports.NavigationService = NavigationService;
});
define("handler/navigation.handler", ["require", "exports"], function (require, exports) {
    "use strict";
    Object.defineProperty(exports, "__esModule", { value: true });
    exports.NavigationHandler = void 0;
    class NavigationHandler {
        constructor(navigationService, controlsBox, rangeDirectSpeed, rangeTurningSpeed) {
            var _a, _b;
            this.navigationService = navigationService;
            this.rangeDirectSpeed = rangeDirectSpeed;
            this.rangeTurningSpeed = rangeTurningSpeed;
            this.visible = true;
            this.leftPWM = 0;
            this.rightPWM = 0;
            this.leftForward = false;
            this.rightForward = false;
            this.movingInterval = null;
            this.isMoving = false;
            this.control_n = controlsBox.querySelector(".N");
            this.control_ne = controlsBox.querySelector(".NE");
            this.control_nw = controlsBox.querySelector(".NW");
            this.control_e = controlsBox.querySelector(".E");
            this.control_w = controlsBox.querySelector(".W");
            this.control_s = controlsBox.querySelector(".S");
            this.control_se = controlsBox.querySelector(".SE");
            this.control_sw = controlsBox.querySelector(".SW");
            this.btnToggle = controlsBox.querySelector(".box__toggle");
            this.innerContainer = controlsBox.querySelector(".navigation__inner");
            this.directSpeedHint = (_a = this.rangeDirectSpeed.nextSibling) === null || _a === void 0 ? void 0 : _a.nextSibling;
            this.turningSpeedHint = (_b = this.rangeTurningSpeed.nextSibling) === null || _b === void 0 ? void 0 : _b.nextSibling;
            this.registerEvents();
        }
        registerEvents() {
            this.registerEvent(this.control_n, 1, 0);
            this.registerEvent(this.control_ne, 1, 1);
            this.registerEvent(this.control_nw, 1, -1);
            this.registerEvent(this.control_e, 0, 1);
            this.registerEvent(this.control_w, 0, -1);
            this.registerEvent(this.control_s, -1, 0);
            this.registerEvent(this.control_se, -1, 1);
            this.registerEvent(this.control_sw, -1, -1);
            this.rangeDirectSpeed.addEventListener('change', (event) => this.directSpeedChange());
            this.rangeTurningSpeed.addEventListener('change', (event) => this.turningSpeedChange());
            this.btnToggle.addEventListener('click', (event) => this.toggleView());
        }
        toggleView() {
            this.visible = !this.visible;
            if (this.visible) {
                this.btnToggle.innerHTML = '&#5169;';
                this.innerContainer.style.display = 'flex';
            }
            else {
                this.btnToggle.innerHTML = '&#5167;';
                this.innerContainer.style.display = 'none';
            }
        }
        registerEvent(control, vertical, horizontal) {
            const functionActivated = (event) => this.activateMotion(event, control, vertical, horizontal);
            const functionDeactivated = () => this.deactivateMotion(control);
            control.addEventListener('touchstart', functionActivated);
            control.addEventListener('mousedown', functionActivated);
            control.addEventListener('touchend', functionDeactivated);
            control.addEventListener('mouseup', functionDeactivated);
        }
        activateMotion(event, control, vertical, horizontal) {
            event.preventDefault();
            event.stopImmediatePropagation();
            control.classList.add('control--pressed');
            this.isMoving = true;
            this.setMotion(vertical, horizontal);
        }
        deactivateMotion(control) {
            control.classList.remove('control--pressed');
            this.isMoving = false;
            if (this.movingInterval)
                clearInterval(this.movingInterval);
            this.movingInterval = null;
            this.navigationService.stop().then(response => console.log(response), error => console.error(error));
        }
        setMotion(vertical, horizontal) {
            this.leftPWM = 0;
            this.rightPWM = 0;
            this.leftForward = false;
            this.rightForward = false;
            const directPwm = Math.round(parseInt(this.rangeDirectSpeed.value) * 2.55);
            const turningPwm = Math.round(parseInt(this.rangeTurningSpeed.value) * 2.55);
            if (vertical == 0) {
                this.leftPWM = this.rightPWM = turningPwm;
                this.leftForward = horizontal > 0;
                this.rightForward = !this.leftForward;
            }
            else {
                this.leftForward = this.rightForward = (vertical > 0);
                this.leftPWM = this.rightPWM = directPwm;
                if (horizontal > 0) {
                    this.rightPWM -= 50;
                }
                else if (horizontal < 0) {
                    this.leftPWM -= 50;
                }
            }
            this.sendMotionCommand();
            if (this.movingInterval)
                clearInterval(this.movingInterval);
            this.movingInterval = setInterval(() => { if (this.isMoving)
                this.sendMotionCommand(); }, 1000);
        }
        sendMotionCommand() {
            this.navigationService.setSpeed(this.leftForward, this.leftPWM, this.rightForward, this.rightPWM).then(response => console.log(response), error => console.error(error));
        }
        directSpeedChange() {
            this.directSpeedHint.textContent = this.rangeDirectSpeed.value + '%';
        }
        turningSpeedChange() {
            this.turningSpeedHint.textContent = this.rangeTurningSpeed.value + '%';
        }
    }
    exports.NavigationHandler = NavigationHandler;
});
define("app", ["require", "exports", "handler/camera.handler", "handler/configuration.handler", "handler/navigation.handler", "handler/streaming.handler", "service/camera.service", "service/configuration.service", "service/http.service", "service/navigation.service"], function (require, exports, camera_handler_1, configuration_handler_1, navigation_handler_1, streaming_handler_1, camera_service_1, configuration_service_1, http_service_1, navigation_service_1) {
    "use strict";
    Object.defineProperty(exports, "__esModule", { value: true });
    const httpService = new http_service_1.HttpService();
    const cameraService = new camera_service_1.CameraService(httpService);
    const navigationService = new navigation_service_1.NavigationService(httpService);
    const configurationService = new configuration_service_1.ConfigurationService(httpService);
    const rangeHorizontal = document.querySelector('#rangeHorizontal');
    const rangeVertical = document.querySelector('#rangeVertical');
    const checkFlashlight = document.querySelector('#chkFlashlight');
    const checkInvHor = document.querySelector('#chkInvHor');
    const checkInvVer = document.querySelector('#chkInvVer');
    const cameraHandler = new camera_handler_1.CameraHandler(cameraService, rangeHorizontal, rangeVertical, checkFlashlight, checkInvHor, checkInvVer);
    const navigationContainer = document.querySelector('#navigationBox');
    const rangeDirectSpeed = document.querySelector('#rangeDirectSpeed');
    const rangeTurningSpeed = document.querySelector('#rangeTurningSpeed');
    const navigationHandler = new navigation_handler_1.NavigationHandler(navigationService, navigationContainer, rangeDirectSpeed, rangeTurningSpeed);
    const viewport = document.querySelector('#streaming-viewport');
    const waitingElement = document.querySelector('#streaming-waiting');
    const streamingHandler = new streaming_handler_1.StreamingHandler(viewport, waitingElement);
    const txtIpAddress = document.querySelector('#txtIpAddress');
    const cmbFrameSize = document.querySelector('#cmbFrameSize');
    const configurationHandler = new configuration_handler_1.ConfigurationHandler(txtIpAddress, cmbFrameSize, configurationService, streamingHandler);
});
