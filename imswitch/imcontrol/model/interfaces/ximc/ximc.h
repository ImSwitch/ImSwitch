#ifndef INC_XIMC_H
#define INC_XIMC_H

/** @file ximc.h
	* \english
	*		@brief Header file for libximc library
	* \endenglish
	* \russian
	*		@brief Заголовочный файл для библиотеки libximc
	* \endrussian
	*/

/** @def XIMC_API
	* \english
	* 		@brief Library import macro.
	* 		Macros allows to automatically import function from shared library.
	* 		It automatically expands to dllimport on msvc when including header file.
	* \endenglish
	* \russian
	*		@brief Макрос импорта библиотеки.
	*		Макросы позволяют автоматически импортировать функцию из общей библиотеки.
	*		Он автоматически расширяется до dllimport на msvc при включении файла заголовка.
	* \endrussian
	*/
#if defined(_WIN32) || defined(LABVIEW64_IMPORT) || defined(LABVIEW32_IMPORT) || defined(MATLAB_IMPORT)
	#define XIMC_API __stdcall
#else
	#ifdef LIBXIMC_EXPORTS
	#define XIMC_API __attribute__((visibility("default")))
	#else
	#define XIMC_API
	#endif
#endif

/** @def XIMC_CALLCONV
	* \english
	*		@brief Library calling convention macros.
	* \endenglish
	* \russian
	*		@brief Библиотека вызывающая условные макросы.
	* \endrussian
	*/
#if defined(_WIN32) || defined(LABVIEW64_IMPORT) || defined(LABVIEW32_IMPORT) || defined(MATLAB_IMPORT)
	#define XIMC_CALLCONV __stdcall
#else
	#define XIMC_CALLCONV
#endif

/** @def XIMC_RETTYPE
	* \english
	* 		@brief Thread return type.
	* \endenglish
	* \russian
	*		@brief Возвращаеемый тип потока.
	* \endrussian
	*/
#if defined(_WIN32) || defined(LABVIEW64_IMPORT) || defined(LABVIEW32_IMPORT) || defined(MATLAB_IMPORT)
#define XIMC_RETTYPE unsigned int
#else
#define XIMC_RETTYPE void*
#endif


#if !defined(XIMC_NO_STDINT)

#if ( (defined(_MSC_VER) && (_MSC_VER < 1600)) || defined(LABVIEW64_IMPORT) || defined(LABVIEW32_IMPORT)) && !defined(MATLAB_IMPORT)
// msvc types burden
typedef __int8 int8_t;
typedef __int16 int16_t;
typedef __int32 int32_t;
typedef __int64 int64_t;
typedef unsigned __int8 uint8_t;
typedef unsigned __int16 uint16_t;
typedef unsigned __int32 uint32_t;
typedef unsigned __int64 uint64_t;
#else
#include <stdint.h>
#endif

/* labview doesn't speak C99 */
#if defined(LABVIEW64_IMPORT) || defined(LABVIEW32_IMPORT)
typedef unsigned __int64 ulong_t;
typedef __int64 long_t;
#else
typedef unsigned long long ulong_t;
typedef long long long_t;
#endif

#endif

#include <time.h>

#if defined(__cplusplus)
extern "C"
{
#endif


	/**
		\english
		* Type describes device identifier
		\endenglish
		\russian
		* Тип идентификатора устройства
		\endrussian
		*/
	typedef int device_t;

	/**
		\english
		* Type specifies result of any operation
		\endenglish
		\russian
		* Тип, определяющий результат выполнения команды.
		\endrussian
		*/
	typedef int result_t;

	/**
		\english
		* Type describes device enumeration structure
		\endenglish
		\russian
		* Тип, определяющий структуру данных о всех контроллерах, обнаруженных при опросе устройств.
		\endrussian
		*/
	#if defined(_WIN64) || defined(__LP64__) || defined(LABVIEW64_IMPORT)
	typedef uint64_t device_enumeration_t;
	#else
	typedef uint32_t device_enumeration_t;
	#endif
	//typedef device_enumeration_t* pdevice_enumeration_t;

	/**
		\english
		* Handle specified undefined device
		\endenglish
		\russian
		* Макрос, означающий неопределенное устройство
		\endrussian
		*/
#define device_undefined -1

	/** \english
		@name Result statuses
		\endenglish
		\russian
		@name Результаты выполнения команд
		\endrussian
		*/
	//@{

	/**
		\english
		* success
		\endenglish
		\russian
		* выполнено успешно
		\endrussian
		*/
#define result_ok 0

	/**
		\english
		* generic error
		\endenglish
		\russian
		* общая ошибка
		\endrussian
		*/
#define result_error -1

	/**
		\english
		* function is not implemented
		\endenglish
		\russian
		* функция не определена
		\endrussian
		*/
#define result_not_implemented -2

	/**
		\english
		* value error
		\endenglish
		\russian
		* ошибка записи значения
		\endrussian
		*/
#define result_value_error -3

	/**
		\english
		* device is lost
		\endenglish
		\russian
		* устройство не подключено
		\endrussian
		*/
#define result_nodevice -4

	//@}

	/** \english
		@name Logging level
		\endenglish
		\russian
		@name Уровень логирования
		\endrussian
		*/
	//@{

	/**
		\english
		* Logging level - error
		\endenglish
		\russian
		* Уровень логирования - ошибка
		\endrussian
		*/
#define LOGLEVEL_ERROR 		0x01
	/**
		\english
		* Logging level - warning
		\endenglish
		\russian
		* Уровень логирования - предупреждение
		\endrussian
		*/
#define LOGLEVEL_WARNING 	0x02
	/**
		\english
		* Logging level - info
		\endenglish
		\russian
		* Уровень логирования - информация
		\endrussian
		*/
#define LOGLEVEL_INFO		0x03
	/**
		\english
		* Logging level - debug
		\endenglish
		\russian
		* Уровень логирования - отладка
		\endrussian
		*/
#define LOGLEVEL_DEBUG		0x04
	//@}


	/**
		\english
		* Calibration companion structure
		\endenglish
		\russian
		* Структура калибровок
		\endrussian	 */
	typedef struct calibration_t
	{
		double A;					/**< Mulitiplier */
		unsigned int MicrostepMode;	/**< Microstep mode */
	} calibration_t;

	/**
		\english
		* Device network information structure.
		\endenglish
		\russian
		* Структура данных с информацией о сетевом устройстве.
		\endrussian	 */
	typedef struct device_network_information_t
	{
		uint32_t ipv4; 				/**< IPv4 address, passed in network byte order (big-endian byte order) */
		char nodename[16];			/**< Name of the Bindy node which hosts the device */
		uint32_t axis_state;		/**< Flags representing device state */
		char locker_username[16];	/**< Name of the user who locked the device (if any) */
		char locker_nodename[16];	/**< Bindy node name, which was used to lock the device (if any) */
		time_t locked_time;			/**< Time the lock was acquired at (UTC, microseconds since the epoch) */
	} device_network_information_t;



/** @cond DO_NOT_WANT */
#define LIBXIMC_VERSION 2.13.5
/** @endcond */


/** @cond DO_NOT_WANT */
#define LIBXIMC_PROTOCOL_VERSION 20.5
/** @endcond */


/*
 ------------------------------------------
   BEGIN OF GENERATED struct declarations
 ------------------------------------------
*/

/** \english
	* @anchor flagset_enumerateflags
	@name Enumerate devices flags
	* This is a bit mask for bitwise operations.
	\endenglish
	\russian
	@name Флаги поиска устройств
	* Это битовая маска для побитовых операций.
	\endrussian
	*/
//@{
#define ENUMERATE_PROBE     0x01 	/**< \english Check if a device with OS name name is XIMC device. Be carefuly with this flag because it sends some data to the device.  \endenglish \russian Проверять, является ли устройство XIMC-совместимым. Будте осторожны с этим флагом, т.к. он отправляет данные в устройство.  \endrussian */
#define ENUMERATE_ALL_COM   0x02 	/**< \english Check all COM devices \endenglish \russian Проверять все COM-устройства \endrussian */
#define ENUMERATE_NETWORK   0x04 	/**< \english Check network devices \endenglish \russian Проверять сетевые устройства \endrussian */
//@}


/**
	* @anchor flagset_movestate
	* \english
	* @name Flags of move state
	* This is a bit mask for bitwise operations.
	* Specify move states.
	* \endenglish
	* \russian
	* @name Флаги состояния движения
	* Это битовая маска для побитовых операций.
	* Возвращаются командой get_status.
	* \endrussian
	* @see get_status
	* @see status_t::MoveSts, get_status_impl
	*/
//@{
#define MOVE_STATE_MOVING         0x01 	/**< \english This flag indicates that controller is trying to move the motor. Don't use this flag for waiting of completion of the movement command. Use MVCMD_RUNNING flag from the MvCmdSts field instead. \endenglish \russian Если флаг установлен, то контроллер пытается вращать двигателем. Не используйте этот флаг для ожидания завершения команды движения. Вместо него используйте MVCMD_RUNNING из поля MvCmdSts. \endrussian */
#define MOVE_STATE_TARGET_SPEED   0x02 	/**< \english Target speed is reached, if flag set. \endenglish \russian Флаг устанавливается при достижении заданной скорости. \endrussian */
#define MOVE_STATE_ANTIPLAY       0x04 	/**< \english Motor is playing compensation, if flag set. \endenglish \russian Выполняется компенсация люфта, если флаг установлен. \endrussian */
//@}


/**
	* @anchor flagset_controllerflags
	* \english
	* @name Flags of internal controller settings
	* This is a bit mask for bitwise operations.
	* \endenglish
	* \russian
	* @name Флаги настроек контроллера
	* Это битовая маска для побитовых операций.
	* \endrussian
	* @see set_controller_name
	* @see get_controller_name
	* @see controller_name_t::CtrlFlags, get_controller_name, set_controller_name
	*/
//@{
#define EEPROM_PRECEDENCE   0x01 	/**< \english If the flag is set settings from external EEPROM override controller settings. \endenglish \russian Если флаг установлен, то настройки в EEPROM подвижки имеют приоритет над текущими настройками и заменяют их при обнаружении EEPROM. \endrussian */
//@}


/**
	* @anchor flagset_powerstate
	* \english
	* @name Flags of power state of stepper motor
	* This is a bit mask for bitwise operations.
	* Specify power states.
	* \endenglish
	* \russian
	* @name Флаги состояния питания шагового мотора
	* Это битовая маска для побитовых операций.
	* Возвращаются командой get_status.
	* \endrussian
	* @see get_status
	* @see status_t::PWRSts, get_status_impl
	*/
//@{
#define PWR_STATE_UNKNOWN   0x00 	/**< \english Unknown state, should never happen. \endenglish \russian Неизвестное состояние, которое не должно никогда реализовываться. \endrussian */
#define PWR_STATE_OFF       0x01 	/**< \english Motor windings are disconnected from the driver. \endenglish \russian Обмотки мотора разомкнуты и не управляются драйвером. \endrussian */
#define PWR_STATE_NORM      0x03 	/**< \english Motor windings are powered by nominal current. \endenglish \russian Обмотки запитаны номинальным током. \endrussian */
#define PWR_STATE_REDUCT    0x04 	/**< \english Motor windings are powered by reduced current to lower power consumption. \endenglish \russian Обмотки намеренно запитаны уменьшенным током от рабочего для снижения потребляемой мощности. \endrussian */
#define PWR_STATE_MAX       0x05 	/**< \english Motor windings are powered by maximum current driver can provide at this voltage. \endenglish \russian Обмотки двигателя питаются от максимального тока, который драйвер может обеспечить при этом напряжении. \endrussian */
//@}


/**
	* @anchor flagset_stateflags
	* \english
	* @name Status flags
	* This is a bit mask for bitwise operations.
	* Controller flags returned by device query.
	* Contains boolean part of controller state.
	* May be combined with bitwise OR.
	* \endenglish
	* \russian
	* @name Флаги состояния
	* Это битовая маска для побитовых операций.
	* Содержат бинарные значения состояния контроллера. Могут быть объединены с помощью логического ИЛИ.
	* \endrussian
	* @see get_status
	* @see status_t::Flags, get_status_impl
	*/
//@{
#define STATE_CONTR                    0x000003F 	/**< \english Flags of controller states. \endenglish \russian Флаги состояния контроллера. \endrussian */
#define STATE_ERRC                     0x0000001 	/**< \english Command error encountered. \endenglish \russian Недопустимая команда. \endrussian */
#define STATE_ERRD                     0x0000002 	/**< \english Data integrity error encountered. \endenglish \russian Нарушение целостности данных. \endrussian */
#define STATE_ERRV                     0x0000004 	/**< \english Value error encountered. \endenglish \russian Недопустимое значение данных. \endrussian */
#define STATE_EEPROM_CONNECTED         0x0000010 	/**< \english EEPROM with settings is connected. \endenglish \russian Подключена память EEPROM с настройками. \endrussian */
#define STATE_IS_HOMED                 0x0000020 	/**< \english Calibration performed \endenglish \russian Калибровка выполнена \endrussian */
#define STATE_SECUR                    0x1B3FFC0 	/**< \english Flags of security. \endenglish \russian Флаги опасности. \endrussian */
#define STATE_ALARM                    0x0000040 	/**< \english Controller is in alarm state indicating that something dangerous had happened. Most commands are ignored in this state. To reset the flag a STOP command must be issued. \endenglish \russian Контроллер находится в состоянии ALARM, показывая, что случилась какая-то опасная ситуация. В состоянии ALARM все команды игнорируются пока не будет послана команда STOP и состояние ALARM деактивируется. \endrussian */
#define STATE_CTP_ERROR                0x0000080 	/**< \english Control position error(is only used with stepper motor). \endenglish \russian Контроль позиции нарушен(используется только с шаговым двигателем). \endrussian */
#define STATE_POWER_OVERHEAT           0x0000100 	/**< \english Power driver overheat. \endenglish \russian Перегрелась силовая часть платы. \endrussian */
#define STATE_CONTROLLER_OVERHEAT      0x0000200 	/**< \english Controller overheat. \endenglish \russian Перегрелась микросхема контроллера. \endrussian */
#define STATE_OVERLOAD_POWER_VOLTAGE   0x0000400 	/**< \english Power voltage exceeds safe limit. \endenglish \russian Превышено напряжение на силовой части. \endrussian */
#define STATE_OVERLOAD_POWER_CURRENT   0x0000800 	/**< \english Power current exceeds safe limit. \endenglish \russian Превышен максимальный ток потребления силовой части. \endrussian */
#define STATE_OVERLOAD_USB_VOLTAGE     0x0001000 	/**< \english USB voltage exceeds safe limit. \endenglish \russian Превышено напряжение на USB. \endrussian */
#define STATE_LOW_USB_VOLTAGE          0x0002000 	/**< \english USB voltage is insufficient for normal operation. \endenglish \russian Слишком низкое напряжение на USB. \endrussian */
#define STATE_OVERLOAD_USB_CURRENT     0x0004000 	/**< \english USB current exceeds safe limit. \endenglish \russian Превышен максимальный ток потребления USB. \endrussian */
#define STATE_BORDERS_SWAP_MISSET      0x0008000 	/**< \english Engine stuck at the wrong edge. \endenglish \russian Достижение неверной границы. \endrussian */
#define STATE_LOW_POWER_VOLTAGE        0x0010000 	/**< \english Power voltage is lower than Low Voltage Protection limit \endenglish \russian Напряжение на силовой части ниже чем напряжение Low Voltage Protection \endrussian */
#define STATE_H_BRIDGE_FAULT           0x0020000 	/**< \english Signal from the driver that fault happened \endenglish \russian Получен сигнал от драйвера о неисправности \endrussian */
#define STATE_WINDING_RES_MISMATCH     0x0100000 	/**< \english The difference between winding resistances is too large \endenglish \russian Сопротивления обмоток отличаются друг от друга слишком сильно \endrussian */
#define STATE_ENCODER_FAULT            0x0200000 	/**< \english Signal from the encoder that fault happened \endenglish \russian Получен сигнал от энкодера о неисправности \endrussian */
#define STATE_ENGINE_RESPONSE_ERROR    0x0800000 	/**< \english Error response of the engine control action. \endenglish \russian Ошибка реакции двигателя на управляющее воздействие. \endrussian */
#define STATE_EXTIO_ALARM              0x1000000 	/**< \english The error is caused by the input signal.. \endenglish \russian Ошибка вызвана входным сигналом. \endrussian */
//@}


/**
	* @anchor flagset_gpioflags
	* \english
	* @name Status flags of the GPIO outputs
	* This is a bit mask for bitwise operations.
	* GPIO state flags returned by device query.
	* Contains boolean part of controller state.
	* May be combined with bitwise OR.
	* \endenglish
	* \russian
	* @name Флаги состояния GPIO входов
	* Это битовая маска для побитовых операций.
	* Содержат бинарные значения состояния контроллера. Могут быть объединены с помощью логического ИЛИ.
	* \endrussian
	* @see get_status
	* @see status_t::GPIOFlags, get_status_impl
	*/
//@{
#define STATE_DIG_SIGNAL     0xFFFF 	/**< \english Flags of digital signals. \endenglish \russian Флаги цифровых сигналов. \endrussian */
#define STATE_RIGHT_EDGE     0x0001 	/**< \english Engine stuck at the right edge. \endenglish \russian Достижение правой границы. \endrussian */
#define STATE_LEFT_EDGE      0x0002 	/**< \english Engine stuck at the left edge. \endenglish \russian Достижение левой границы. \endrussian */
#define STATE_BUTTON_RIGHT   0x0004 	/**< \english Button "right" state (1 if pressed). \endenglish \russian Состояние кнопки "вправо" (1, если нажата). \endrussian */
#define STATE_BUTTON_LEFT    0x0008 	/**< \english Button "left" state (1 if pressed). \endenglish \russian Состояние кнопки "влево" (1, если нажата). \endrussian */
#define STATE_GPIO_PINOUT    0x0010 	/**< \english External GPIO works as Out, if flag set; otherwise works as In. \endenglish \russian Если флаг установлен, ввод/вывод общего назначения работает как выход; если флаг сброшен, ввод/вывод работает как вход. \endrussian */
#define STATE_GPIO_LEVEL     0x0020 	/**< \english State of external GPIO pin. \endenglish \russian Состояние ввода/вывода общего назначения. \endrussian */
#define STATE_BRAKE          0x0200 	/**< \english State of Brake pin. Flag "1" - if the pin state brake is not powered(brake is clamped), "0" - if the pin state brake is powered(brake is unclamped). \endenglish \russian Состояние вывода управления тормозом. Флаг "1" - если тормоз не запитан(зажат), "0" - если на тормоз подаётся питание(разжат). \endrussian */
#define STATE_REV_SENSOR     0x0400 	/**< \english State of Revolution sensor pin. \endenglish \russian Состояние вывода датчика оборотов(флаг "1", если датчик активен). \endrussian */
#define STATE_SYNC_INPUT     0x0800 	/**< \english State of Sync input pin. \endenglish \russian Состояние входа синхронизации(1, если вход синхронизации активен). \endrussian */
#define STATE_SYNC_OUTPUT    0x1000 	/**< \english State of Sync output pin. \endenglish \russian Состояние выхода синхронизации(1, если выход синхронизации активен). \endrussian */
#define STATE_ENC_A          0x2000 	/**< \english State of encoder A pin. \endenglish \russian Состояние ножки A энкодера(флаг "1", если энкодер активен). \endrussian */
#define STATE_ENC_B          0x4000 	/**< \english State of encoder B pin. \endenglish \russian Состояние ножки B энкодера(флаг "1", если энкодер активен). \endrussian */
//@}


/**
	* @anchor flagset_encodestatus
	* \english
	* @name Encoder state
	* This is a bit mask for bitwise operations.
	* Encoder state returned by device query.
	* \endenglish
	* \russian
	* @name Состояние энкодера
	* Это битовая маска для побитовых операций.
	* Состояние энкодера, подключенного к контроллеру.
	* \endrussian
	* @see get_status
	* @see status_t::EncSts, get_status_impl
	*/
//@{
#define ENC_STATE_ABSENT    0x00 	/**< \english Encoder is absent. \endenglish \russian Энкодер не подключен. \endrussian */
#define ENC_STATE_UNKNOWN   0x01 	/**< \english Encoder state is unknown. \endenglish \russian Cостояние энкодера неизвестно. \endrussian */
#define ENC_STATE_MALFUNC   0x02 	/**< \english Encoder is connected and malfunctioning. \endenglish \russian Энкодер подключен и неисправен. \endrussian */
#define ENC_STATE_REVERS    0x03 	/**< \english Encoder is connected and operational but counts in other direction. \endenglish \russian Энкодер подключен и исправен, но считает в другую сторону. \endrussian */
#define ENC_STATE_OK        0x04 	/**< \english Encoder is connected and working properly. \endenglish \russian Энкодер подключен и работает должным образом. \endrussian */
//@}


/**
	* @anchor flagset_windstatus
	* \english
	* @name Winding state
	* This is a bit mask for bitwise operations.
	* Motor winding state returned by device query.
	* \endenglish
	* \russian
	* @name Состояние обмоток
	* Это битовая маска для побитовых операций.
	* Состояние обмоток двигателя, подключенного к контроллеру.
	* \endrussian
	* @see get_status
	* @see status_t::WindSts, get_status_impl
	*/
//@{
#define WIND_A_STATE_ABSENT    0x00 	/**< \english Winding A is disconnected. \endenglish \russian Обмотка A не подключена. \endrussian */
#define WIND_A_STATE_UNKNOWN   0x01 	/**< \english Winding A state is unknown. \endenglish \russian Cостояние обмотки A неизвестно. \endrussian */
#define WIND_A_STATE_MALFUNC   0x02 	/**< \english Winding A is short-circuited. \endenglish \russian Короткое замыкание на обмотке A. \endrussian */
#define WIND_A_STATE_OK        0x03 	/**< \english Winding A is connected and working properly. \endenglish \russian Обмотка A работает адекватно. \endrussian */
#define WIND_B_STATE_ABSENT    0x00 	/**< \english Winding B is disconnected. \endenglish \russian Обмотка B не подключена. \endrussian */
#define WIND_B_STATE_UNKNOWN   0x10 	/**< \english Winding B state is unknown. \endenglish \russian Cостояние обмотки B неизвестно. \endrussian */
#define WIND_B_STATE_MALFUNC   0x20 	/**< \english Winding B is short-circuited. \endenglish \russian Короткое замыкание на обмотке B. \endrussian */
#define WIND_B_STATE_OK        0x30 	/**< \english Winding B is connected and working properly. \endenglish \russian Обмотка B работает адекватно. \endrussian */
//@}


/**
	* @anchor flagset_mvcmdstatus
	* \english
	* @name Move command state
	* This is a bit mask for bitwise operations.
	* Move command (command_move, command_movr, command_left, command_right, command_stop, command_home, command_loft, command_sstp)
	* and its state (run, finished, error).
	* \endenglish
	* \russian
	* @name Состояние команды движения
	* Это битовая маска для побитовых операций.
	* Состояние команды движения (касается command_move, command_movr, command_left, command_right, command_stop, command_home, command_loft, command_sstp)
	* и статуса её выполнения (выполяется, завершено, ошибка)
	* \endrussian
	* @see get_status
	* @see status_t::MvCmdSts, get_status_impl
	*/
//@{
#define MVCMD_NAME_BITS   0x3F 	/**< \english Move command bit mask. \endenglish \russian Битовая маска активной команды. \endrussian */
#define MVCMD_UKNWN       0x00 	/**< \english Unknown command. \endenglish \russian Неизвестная команда. \endrussian */
#define MVCMD_MOVE        0x01 	/**< \english Command move. \endenglish \russian Команда move. \endrussian */
#define MVCMD_MOVR        0x02 	/**< \english Command movr. \endenglish \russian Команда movr. \endrussian */
#define MVCMD_LEFT        0x03 	/**< \english Command left. \endenglish \russian Команда left. \endrussian */
#define MVCMD_RIGHT       0x04 	/**< \english Command rigt. \endenglish \russian Команда rigt. \endrussian */
#define MVCMD_STOP        0x05 	/**< \english Command stop. \endenglish \russian Команда stop. \endrussian */
#define MVCMD_HOME        0x06 	/**< \english Command home. \endenglish \russian Команда home. \endrussian */
#define MVCMD_LOFT        0x07 	/**< \english Command loft. \endenglish \russian Команда loft. \endrussian */
#define MVCMD_SSTP        0x08 	/**< \english Command soft stop. \endenglish \russian Команда плавной остановки(SSTP). \endrussian */
#define MVCMD_ERROR       0x40 	/**< \english Finish state (1 - move command have finished with an error, 0 - move command have finished correctly). This flags is actual when MVCMD_RUNNING signals movement finish. \endenglish \russian Состояние завершения движения (1 - команда движения выполнена с ошибкой, 0 - команда движения выполнена корректно). Имеет смысл если MVCMD_RUNNING указывает на завершение движения. \endrussian */
#define MVCMD_RUNNING     0x80 	/**< \english Move command state (0 - move command have finished, 1 - move command is being executed). \endenglish \russian Состояние команды движения (0 - команда движения выполнена, 1 - команда движения сейчас выполняется). \endrussian */
//@}


/**
	* @anchor flagset_moveflags
	* \english
	* @name Flags of the motion parameters
	* This is a bit mask for bitwise operations.
	* Specify motor shaft movement algorithm and list of limitations.
	* Flags returned by query of get_move_settings.
	* \endenglish
	* \russian
	* @name Флаги параметров движения
	* Это битовая маска для побитовых операций.
	* Определяют настройки параметров движения.
	* Возращаются командой get_move_settings.
	* \endrussian
	* @see set_move_settings
	* @see get_move_settings
	* @see move_settings_t::MoveFlags, get_move_settings, set_move_settings
	*/
//@{
#define RPM_DIV_1000   0x01 	/**< \english This flag indicates that the operating speed specified in the command is set in milli rpm. Applicable only for ENCODER feedback mode and only for BLDC motors. \endenglish \russian Флаг указывает на то что рабочая скорость указанная в команде задана в милли rpm. Применим только для режима обратной связи ENCODER и только для BLDC моторов. \endrussian */
//@}


/**
	* @anchor flagset_engineflags
	* \english
	* @name Flags of engine settings
	* This is a bit mask for bitwise operations.
	* Specify motor shaft movement algorithm and list of limitations.
	* Flags returned by query of engine settings. May be combined with bitwise OR.
	* \endenglish
	* \russian
	* @name Флаги параметров мотора
	* Это битовая маска для побитовых операций.
	* Определяют настройки движения и работу ограничителей.
	* Возращаются командой get_engine_settings. Могут быть объединены с помощью логического ИЛИ.
	* \endrussian
	* @see set_engine_settings
	* @see get_engine_settings
	* @see engine_settings_t::EngineFlags, get_engine_settings, set_engine_settings
	*/
//@{
#define ENGINE_REVERSE          0x01 	/**< \english Reverse flag. It determines motor shaft rotation direction that corresponds to feedback counts increasing. If not set (default), motor shaft rotation direction under positive voltage corresponds to feedback counts increasing and vice versa. Change it if you see that positive directions on motor and feedback are opposite. \endenglish \russian Флаг реверса. Связывает направление вращения мотора с направлением счета текущей позиции. При сброшенном флаге (по умолчанию) прикладываемое к мотору положительное напряжение увеличивает счетчик позиции. И наоборот, при установленном флаге счетчик позиции увеличивается, когда к мотору приложено отрицательное напряжение. Измените состояние флага, если положительное вращение мотора уменьшает счетчик позиции. \endrussian */
#define ENGINE_CURRENT_AS_RMS   0x02 	/**< \english Engine current meaning flag. If the flag is unset, then engine current value is interpreted as maximum amplitude value. If the flag is set, then engine current value is interpreted as root mean square current value (for stepper) or as the current value calculated from the maximum heat dissipation (bldc). \endenglish \russian Флаг интерпретации значения тока. Если флаг снят, то задаваемое значение тока интерпретируется как максимальная амплитуда тока. Если флаг установлен, то задаваемое значение тока интерпретируется как среднеквадратичное значение тока (для шагового) или как значение тока, посчитанное из максимального тепловыделения (bldc). \endrussian */
#define ENGINE_MAX_SPEED        0x04 	/**< \english Max speed flag. If it is set, engine uses maximum speed achievable with the present engine settings as nominal speed. \endenglish \russian Флаг максимальной скорости. Если флаг установлен, движение происходит на максимальной скорости. \endrussian */
#define ENGINE_ANTIPLAY         0x08 	/**< \english Play compensation flag. If it set, engine makes backlash (play) compensation procedure and reach the predetermined position accurately on low speed. \endenglish \russian Компенсация люфта. Если флаг установлен, позиционер будет подходить к заданной точке всегда с одной стороны. Например, при подходе слева никаких дополнительных действий не совершается, а при подходе справа позиционер проходит целевую позицию на заданное расстояния и возвращается к ней опять же справа. \endrussian */
#define ENGINE_ACCEL_ON         0x10 	/**< \english Acceleration enable flag. If it set, motion begins with acceleration and ends with deceleration. \endenglish \russian Ускорение. Если флаг установлен, движение происходит с ускорением. \endrussian */
#define ENGINE_LIMIT_VOLT       0x20 	/**< \english Maximum motor voltage limit enable flag(is only used with DC motor). \endenglish \russian Номинальное напряжение мотора. Если флаг установлен, напряжение на моторе ограничивается заданным номинальным значением(используется только с DC двигателем). \endrussian */
#define ENGINE_LIMIT_CURR       0x40 	/**< \english Maximum motor current limit enable flag(is only used with DC motor). \endenglish \russian Номинальный ток мотора. Если флаг установлен, ток через мотор ограничивается заданным номинальным значением(используется только с DC двигателем). \endrussian */
#define ENGINE_LIMIT_RPM        0x80 	/**< \english Maximum motor speed limit enable flag. \endenglish \russian Номинальная частота вращения мотора. Если флаг установлен, частота вращения ограничивается заданным номинальным значением. \endrussian */
//@}


/**
	* @anchor flagset_microstepmode
	* \english
	* @name Flags of microstep mode
	* This is a bit mask for bitwise operations.
	* Specify settings of microstep mode. Using with step motors.
	* Flags returned by query of engine settings. May be combined with bitwise OR
	* \endenglish
	* \russian
	* @name Флаги параметров микрошагового режима
	* Это битовая маска для побитовых операций.
	* Определяют деление шага в микрошаговом режиме. Используются с шаговыми моторами.
	* Возращаются командой get_engine_settings. Могут быть объединены с помощью логического ИЛИ.
	* \endrussian
	* @see engine_settings_t::flags
	* @see set_engine_settings
	* @see get_engine_settings
	* @see engine_settings_t::MicrostepMode, get_engine_settings, set_engine_settings
	*/
//@{
#define MICROSTEP_MODE_FULL       0x01 	/**< \english Full step mode. \endenglish \russian Полношаговый режим. \endrussian */
#define MICROSTEP_MODE_FRAC_2     0x02 	/**< \english 1/2 step mode. \endenglish \russian Деление шага 1/2. \endrussian */
#define MICROSTEP_MODE_FRAC_4     0x03 	/**< \english 1/4 step mode. \endenglish \russian Деление шага 1/4. \endrussian */
#define MICROSTEP_MODE_FRAC_8     0x04 	/**< \english 1/8 step mode. \endenglish \russian Деление шага 1/8. \endrussian */
#define MICROSTEP_MODE_FRAC_16    0x05 	/**< \english 1/16 step mode. \endenglish \russian Деление шага 1/16. \endrussian */
#define MICROSTEP_MODE_FRAC_32    0x06 	/**< \english 1/32 step mode. \endenglish \russian Деление шага 1/32. \endrussian */
#define MICROSTEP_MODE_FRAC_64    0x07 	/**< \english 1/64 step mode. \endenglish \russian Деление шага 1/64. \endrussian */
#define MICROSTEP_MODE_FRAC_128   0x08 	/**< \english 1/128 step mode. \endenglish \russian Деление шага 1/128. \endrussian */
#define MICROSTEP_MODE_FRAC_256   0x09 	/**< \english 1/256 step mode. \endenglish \russian Деление шага 1/256. \endrussian */
//@}


/**
	* @anchor flagset_enginetype
	* \english
	* @name Flags of engine type
	* This is a bit mask for bitwise operations.
	* Specify motor type.
	* Flags returned by query of engine settings.
	* \endenglish
	* \russian
	* @name Флаги, определяющие тип мотора
	* Это битовая маска для побитовых операций.
	* Определяют тип мотора.
	* Возращаются командой get_entype_settings.
	* \endrussian
	* @see engine_settings_t::flags
	* @see set_entype_settings
	* @see get_entype_settings
	* @see entype_settings_t::EngineType, get_entype_settings, set_entype_settings
	*/
//@{
#define ENGINE_TYPE_NONE        0x00 	/**< \english A value that shouldn't be used. \endenglish \russian Это значение не нужно использовать. \endrussian */
#define ENGINE_TYPE_DC          0x01 	/**< \english DC motor. \endenglish \russian Мотор постоянного тока. \endrussian */
#define ENGINE_TYPE_2DC         0x02 	/**< \english 2 DC motors. \endenglish \russian Два мотора постоянного тока, что приводит к эмуляции двух контроллеров. \endrussian */
#define ENGINE_TYPE_STEP        0x03 	/**< \english Step motor. \endenglish \russian Шаговый мотор. \endrussian */
#define ENGINE_TYPE_TEST        0x04 	/**< \english Duty cycle are fixed. Used only manufacturer. \endenglish \russian Продолжительность включения фиксирована. Используется только производителем. \endrussian */
#define ENGINE_TYPE_BRUSHLESS   0x05 	/**< \english Brushless motor. \endenglish \russian Бесщеточный мотор. \endrussian */
//@}


/**
	* @anchor flagset_drivertype
	* \english
	* @name Flags of driver type
	* This is a bit mask for bitwise operations.
	* Specify driver type.
	* Flags returned by query of engine settings.
	* \endenglish
	* \russian
	* @name Флаги, определяющие тип силового драйвера
	* Это битовая маска для побитовых операций.
	* Определяют тип силового драйвера.
	* Возращаются командой get_entype_settings.
	* \endrussian
	* @see engine_settings_t::flags
	* @see set_entype_settings
	* @see get_entype_settings
	* @see entype_settings_t::DriverType, get_entype_settings, set_entype_settings
	*/
//@{
#define DRIVER_TYPE_DISCRETE_FET   0x01 	/**< \english Driver with discrete FET keys. Default option. \endenglish \russian Силовой драйвер на дискретных мосфет-ключах. Используется по умолчанию. \endrussian */
#define DRIVER_TYPE_INTEGRATE      0x02 	/**< \english Driver with integrated IC. \endenglish \russian Силовой драйвер с использованием ключей, интегрированных в микросхему. \endrussian */
#define DRIVER_TYPE_EXTERNAL       0x03 	/**< \english External driver. \endenglish \russian Внешний силовой драйвер. \endrussian */
//@}


/**
	* @anchor flagset_powerflags
	* \english
	* @name Flags of power settings of stepper motor
	* This is a bit mask for bitwise operations.
	* Flags returned by query of engine settings.
	* Specify power settings. Flags returned by query of power settings.
	* \endenglish
	* \russian
	* @name Флаги параметров питания шагового мотора
	* Это битовая маска для побитовых операций.
	* Возвращаются командой get_power_settings.
	* \endrussian
	* @see get_power_settings
	* @see set_power_settings
	* @see power_settings_t::PowerFlags, get_power_settings, set_power_settings
	*/
//@{
#define POWER_REDUCT_ENABLED   0x01 	/**< \english Current reduction enabled after CurrReductDelay, if this flag is set. \endenglish \russian Если флаг установлен, уменьшить ток по прошествии CurrReductDelay. Иначе - не уменьшать. \endrussian */
#define POWER_OFF_ENABLED      0x02 	/**< \english Power off enabled after PowerOffDelay, if this flag is set. \endenglish \russian Если флаг установлен, снять напряжение с обмоток по прошествии PowerOffDelay. Иначе - не снимать. \endrussian */
#define POWER_SMOOTH_CURRENT   0x04 	/**< \english Current ramp-up/down is performed smoothly during current_set_time, if this flag is set. \endenglish \russian Если установлен, то запитывание обмоток, снятие питания или снижение/повышение тока происходят плавно со скоростью CurrentSetTime, а только потом выполняется та задача, которая вызвала это плавное изменение. \endrussian */
//@}


/**
	* @anchor flagset_secureflags
	* \english
	* @name Flags of secure settings
	* This is a bit mask for bitwise operations.
	* Flags returned by query of engine settings.
	* Specify secure settings. Flags returned by query of secure settings.
	* \endenglish
	* \russian
	* @name Флаги критических параметров.
	* Это битовая маска для побитовых операций.
	* Возвращаются командой get_secure_settings.
	* \endrussian
	* @see get_secure_settings
	* @see set_secure_settings
	* @see secure_settings_t::Flags, get_secure_settings, set_secure_settings
	*/
//@{
#define ALARM_ON_DRIVER_OVERHEATING    0x01 	/**< \english If this flag is set enter Alarm state on driver overheat signal. \endenglish \russian Если флаг установлен, то войти в состояние Alarm при получении сигнала подступающего перегрева с драйвера. Иначе - игнорировать подступающий перегрев с драйвера. \endrussian */
#define LOW_UPWR_PROTECTION            0x02 	/**< \english If this flag is set turn off motor when voltage is lower than LowUpwrOff. \endenglish \russian Если установлен, то выключать силовую часть при напряжении меньшем LowUpwrOff. \endrussian */
#define H_BRIDGE_ALERT                 0x04 	/**< \english If this flag is set then turn off the power unit with a signal problem in one of the transistor bridge. \endenglish \russian Если установлен, то выключать силовую часть при сигнале неполадки в одном из транзисторных мостов.\endrussian */
#define ALARM_ON_BORDERS_SWAP_MISSET   0x08 	/**< \english If this flag is set enter Alarm state on borders swap misset \endenglish \russian Если флаг установлен, то войти в состояние Alarm при получении сигнала c противоположного концевика.\endrussian */
#define ALARM_FLAGS_STICKING           0x10 	/**< \english If this flag is set only a STOP command can turn all alarms to 0 \endenglish \russian Если флаг установлен, то только по команде STOP возможен сброс всех флагов ALARM.\endrussian */
#define USB_BREAK_RECONNECT            0x20 	/**< \english If this flag is set USB brake reconnect module will be enable \endenglish \russian Если флаг установлен, то будет включен блок перезагрузки USB при поломке связи.\endrussian */
#define ALARM_WINDING_MISMATCH         0x40 	/**< \english If this flag is set enter Alarm state when windings mismatch \endenglish \russian Если флаг установлен, то войти в состояние Alarm при получении сигнала рассогласования обмоток \endrussian */
#define ALARM_ENGINE_RESPONSE          0x80 	/**< \english If this flag is set enter Alarm state on response of the engine control action \endenglish \russian Если флаг установлен, то войти в состояние Alarm при получении сигнала ошибки реакции двигателя на управляющее воздействие  \endrussian */
//@}


/**
	* @anchor flagset_positionflags
	* \english
	* @name Position setting flags
	* This is a bit mask for bitwise operations.
	* Flags used in setting of position.
	* \endenglish
	* \russian
	* @name Флаги установки положения
	* Это битовая маска для побитовых операций.
	* Возвращаются командой get_position.
	* \endrussian
	* @see get_position
	* @see set_position
	* @see set_position_t::PosFlags, set_position
	*/
//@{
#define SETPOS_IGNORE_POSITION   0x01 	/**< \english Will not reload position in steps/microsteps if this flag is set. \endenglish \russian Если установлен, то позиция в шагах и микрошагах не обновляется. \endrussian */
#define SETPOS_IGNORE_ENCODER    0x02 	/**< \english Will not reload encoder state if this flag is set. \endenglish \russian Если установлен, то счётчик энкодера не обновляется. \endrussian */
//@}


/**
	* @anchor flagset_feedbacktype
	* \english
	* @name Feedback type.
	* This is a bit mask for bitwise operations.
	* \endenglish
	* \russian
	* @name Тип обратной связи.
	* Это битовая маска для побитовых операций.
	* \endrussian
	* @see set_feedback_settings
	* @see get_feedback_settings
	* @see feedback_settings_t::FeedbackType, get_feedback_settings, set_feedback_settings
	*/
//@{
#define FEEDBACK_ENCODER            0x01 	/**< \english Feedback by encoder. \endenglish \russian Обратная связь с помощью энкодера. \endrussian */
#define FEEDBACK_EMF                0x04 	/**< \english Feedback by EMF. \endenglish \russian Обратная связь по ЭДС. \endrussian */
#define FEEDBACK_NONE               0x05 	/**< \english Feedback is absent. \endenglish \russian Обратная связь отсутствует. \endrussian */
#define FEEDBACK_ENCODER_MEDIATED   0x06 	/**< \english Feedback by encoder mediated by mechanical transmission (for example leadscrew). \endenglish \russian Обратная связь по энкодеру, опосредованному относительно двигателя механической передачей (например, винтовой передачей). \endrussian */
//@}


/**
	* @anchor flagset_feedbackflags
	* \english
	* @name Describes feedback flags.
	* This is a bit mask for bitwise operations.
	* \endenglish
	* \russian
	* @name Флаги обратной связи.
	* Это битовая маска для побитовых операций.
	* \endrussian
	* @see set_feedback_settings
	* @see get_feedback_settings
	* @see feedback_settings_t::FeedbackFlags, get_feedback_settings, set_feedback_settings
	*/
//@{
#define FEEDBACK_ENC_REVERSE             0x01 	/**< \english Reverse count of encoder. \endenglish \russian Обратный счет у энкодера. \endrussian */
#define FEEDBACK_ENC_TYPE_BITS           0xC0 	/**< \english Bits of the encoder type. \endenglish \russian Биты, отвечающие за тип энкодера. \endrussian */
#define FEEDBACK_ENC_TYPE_AUTO           0x00 	/**< \english Auto detect encoder type. \endenglish \russian Определяет тип энкодера автоматически. \endrussian */
#define FEEDBACK_ENC_TYPE_SINGLE_ENDED   0x40 	/**< \english Single ended encoder. \endenglish \russian Недифференциальный энкодер. \endrussian */
#define FEEDBACK_ENC_TYPE_DIFFERENTIAL   0x80 	/**< \english Differential encoder. \endenglish \russian Дифференциальный энкодер. \endrussian */
//@}


/**
	* @anchor flagset_syncinflags
	* \english
	* @name Flags for synchronization input setup
	* This is a bit mask for bitwise operations.
	* \endenglish
	* \russian
	* @name Флаги настроек синхронизации входа
	* Это битовая маска для побитовых операций.
	* \endrussian
	* @see sync_in_settings_t::SyncInFlags, get_sync_in_settings, set_sync_in_settings
	*/
//@{
#define SYNCIN_ENABLED        0x01 	/**< \english Synchronization in mode is enabled, if this flag is set. \endenglish \russian Включение необходимости импульса синхронизации для начала движения. \endrussian */
#define SYNCIN_INVERT         0x02 	/**< \english Trigger on falling edge if flag is set, on rising edge otherwise. \endenglish \russian Если установлен - срабатывает по переходу из 1 в 0. Иначе - из 0 в 1. \endrussian */
#define SYNCIN_GOTOPOSITION   0x04 	/**< \english The engine is go to position specified in Position and uPosition, if this flag is set. And it is shift on the Position and uPosition, if this flag is unset \endenglish \russian Если флаг установлен, то двигатель смещается к позиции, установленной в Position и uPosition, иначе двигатель смещается на Position и uPosition \endrussian */
//@}


/**
	* @anchor flagset_syncoutflags
	* \english
	* @name Flags of synchronization output
	* This is a bit mask for bitwise operations.
	* \endenglish
	* \russian
	* @name Флаги настроек синхронизации выхода
	* Это битовая маска для побитовых операций.
	* \endrussian
	* @see sync_out_settings_t::SyncOutFlags, get_sync_out_settings, set_sync_out_settings
	*/
//@{
#define SYNCOUT_ENABLED    0x01 	/**< \english Synchronization out pin follows the synchronization logic, if set. It governed by SYNCOUT_STATE flag otherwise. \endenglish \russian Синхронизация выхода работает согласно настройкам, если флаг установлен. В ином случае значение выхода фиксировано и подчиняется SYNCOUT_STATE. \endrussian */
#define SYNCOUT_STATE      0x02 	/**< \english When output state is fixed by negative SYNCOUT_ENABLED flag, the pin state is in accordance with this flag state. \endenglish \russian Когда значение выхода управляется напрямую (см. флаг SYNCOUT_ENABLED), значение на выходе соответствует значению этого флага. \endrussian */
#define SYNCOUT_INVERT     0x04 	/**< \english Low level is active, if set, and high level is active otherwise. \endenglish \russian Нулевой логический уровень является активным, если флаг установлен, а единичный - если флаг сброшен. \endrussian */
#define SYNCOUT_IN_STEPS   0x08 	/**< \english Use motor steps/encoder pulses instead of milliseconds for output pulse generation if the flag is set. \endenglish \russian Если флаг установлен использовать шаги/импульсы энкодера для выходных импульсов синхронизации вместо миллисекунд. \endrussian */
#define SYNCOUT_ONSTART    0x10 	/**< \english Generate synchronization pulse when movement starts. \endenglish \russian Генерация синхронизирующего импульса при начале движения. \endrussian */
#define SYNCOUT_ONSTOP     0x20 	/**< \english Generate synchronization pulse when movement stops. \endenglish \russian Генерация синхронизирующего импульса при остановке. \endrussian */
#define SYNCOUT_ONPERIOD   0x40 	/**< \english Generate synchronization pulse every SyncOutPeriod encoder pulses. \endenglish \russian Выдает импульс синхронизации после прохождения SyncOutPeriod отсчётов. \endrussian */
//@}


/**
	* @anchor flagset_extiosetupflags
	* \english
	* @name External IO setup flags
	* This is a bit mask for bitwise operations.
	* \endenglish
	* \russian
	* @name Флаги настройки работы внешнего ввода/вывода
	* Это битовая маска для побитовых операций.
	* \endrussian
	* @see get_extio_settings
	* @see set_extio_settings
	* @see extio_settings_t::EXTIOSetupFlags, get_extio_settings, set_extio_settings
	*/
//@{
#define EXTIO_SETUP_OUTPUT   0x01 	/**< \english EXTIO works as output if flag is set, works as input otherwise. \endenglish \russian Если флаг установлен, то ножка в состоянии вывода, иначе - ввода. \endrussian */
#define EXTIO_SETUP_INVERT   0x02 	/**< \english Interpret EXTIO states and fronts inverted if flag is set. Falling front as input event and low logic level as active state. \endenglish \russian Eсли флаг установлен, то нули считаются активным состоянием выхода, а спадающие фронты как момент подачи входного сигнала. \endrussian */
//@}


/**
	* @anchor flagset_extiomodeflags
	* \english
	* @name External IO mode flags
	* This is a bit mask for bitwise operations.
	* \endenglish
	* \russian
	* @name Флаги настройки режимов внешнего ввода/вывода
	* Это битовая маска для побитовых операций.
	* \endrussian
	* @see extio_settings_t::extio_mode_flags
	* @see get_extio_settings
	* @see set_extio_settings
	* @see extio_settings_t::EXTIOModeFlags, get_extio_settings, set_extio_settings
	*/
//@{
#define EXTIO_SETUP_MODE_IN_BITS        0x0F 	/**< \english Bits of the behaviour selector when the signal on input goes to the active state. \endenglish \russian Биты, отвечающие за поведение при переходе сигнала в активное состояние. \endrussian */
#define EXTIO_SETUP_MODE_IN_NOP         0x00 	/**< \english Do nothing. \endenglish \russian Ничего не делать. \endrussian */
#define EXTIO_SETUP_MODE_IN_STOP        0x01 	/**< \english Issue STOP command, ceasing the engine movement. \endenglish \russian По переднему фронту входного сигнала делается остановка двигателя (эквивалент команды STOP). \endrussian */
#define EXTIO_SETUP_MODE_IN_PWOF        0x02 	/**< \english Issue PWOF command, powering off all engine windings. \endenglish \russian Выполняет команду PWOF, обесточивая обмотки двигателя. \endrussian */
#define EXTIO_SETUP_MODE_IN_MOVR        0x03 	/**< \english Issue MOVR command with last used settings. \endenglish \russian Выполняется команда MOVR с последними настройками. \endrussian */
#define EXTIO_SETUP_MODE_IN_HOME        0x04 	/**< \english Issue HOME command. \endenglish \russian Выполняется команда HOME. \endrussian */
#define EXTIO_SETUP_MODE_IN_ALARM       0x05 	/**< \english Set Alarm when the signal goes to the active state. \endenglish \russian Войти в состояние ALARM при переходе сигнала в активное состояние. \endrussian */
#define EXTIO_SETUP_MODE_OUT_BITS       0xF0 	/**< \english Bits of the output behaviour selection. \endenglish \russian Биты выбора поведения на выходе. \endrussian */
#define EXTIO_SETUP_MODE_OUT_OFF        0x00 	/**< \english EXTIO pin always set in inactive state. \endenglish \russian Ножка всегда в неактивном состоянии. \endrussian */
#define EXTIO_SETUP_MODE_OUT_ON         0x10 	/**< \english EXTIO pin always set in active state. \endenglish \russian Ножка всегда в активном состоянии. \endrussian */
#define EXTIO_SETUP_MODE_OUT_MOVING     0x20 	/**< \english EXTIO pin stays active during moving state. \endenglish \russian Ножка находится в активном состоянии при движении. \endrussian */
#define EXTIO_SETUP_MODE_OUT_ALARM      0x30 	/**< \english EXTIO pin stays active during Alarm state. \endenglish \russian Ножка находится в активном состоянии при нахождении в состоянии ALARM. \endrussian */
#define EXTIO_SETUP_MODE_OUT_MOTOR_ON   0x40 	/**< \english EXTIO pin stays active when windings are powered. \endenglish \russian Ножка находится в активном состоянии при подаче питания на обмотки. \endrussian */
//@}


/**
	* @anchor flagset_borderflags
	* \english
	* @name Border flags
	* This is a bit mask for bitwise operations.
	* Specify types of borders and motor behaviour on borders.
	* May be combined with bitwise OR.
	* \endenglish
	* \russian
	* @name Флаги границ
	* Это битовая маска для побитовых операций.
	* Типы границ и поведение позиционера на границах.
	* Могут быть объединены с помощью побитового ИЛИ.
	* \endrussian
	* @see get_edges_settings
	* @see set_edges_settings
	* @see edges_settings_t::BorderFlags, get_edges_settings, set_edges_settings
	*/
//@{
#define BORDER_IS_ENCODER               0x01 	/**< \english Borders are fixed by predetermined encoder values, if set; borders position on limit switches, if not set. \endenglish \russian Если флаг установлен, границы определяются предустановленными точками на шкале позиции. Если флаг сброшен, границы определяются концевыми выключателями. \endrussian */
#define BORDER_STOP_LEFT                0x02 	/**< \english Motor should stop on left border. \endenglish \russian Если флаг установлен, мотор останавливается при достижении левой границы. \endrussian */
#define BORDER_STOP_RIGHT               0x04 	/**< \english Motor should stop on right border. \endenglish \russian Если флаг установлен, мотор останавливается при достижении правой границы. \endrussian */
#define BORDERS_SWAP_MISSET_DETECTION   0x08 	/**< \english Motor should stop on both borders. Need to save motor then wrong border settings is set\endenglish \russian Если флаг установлен, мотор останавливается при достижении обоих границ. Нужен для предотвращения поломки двигателя при неправильных настройках концевиков \endrussian */
//@}


/**
	* @anchor flagset_enderflags
	* \english
	* @name Limit switches flags
	* This is a bit mask for bitwise operations.
	* Specify electrical behaviour of limit switches like order and pulled positions.
	* May be combined with bitwise OR.
	* \endenglish
	* \russian
	* @name Флаги концевых выключателей
	* Это битовая маска для побитовых операций.
	* Определяют направление и состояние границ.
	* Могут быть объединены с помощью побитового ИЛИ.
	* \endrussian
	* @see get_edges_settings
	* @see set_edges_settings
	* @see edges_settings_t::EnderFlags, get_edges_settings, set_edges_settings
	*/
//@{
#define ENDER_SWAP             0x01 	/**< \english First limit switch on the right side, if set; otherwise on the left side. \endenglish \russian Если флаг установлен, первый концевой выключатель находится справа; иначе - слева. \endrussian */
#define ENDER_SW1_ACTIVE_LOW   0x02 	/**< \english 1 - Limit switch connnected to pin SW1 is triggered by a low level on pin. \endenglish \russian 1 - Концевик, подключенный к ножке SW1, считается сработавшим по низкому уровню на контакте. \endrussian */
#define ENDER_SW2_ACTIVE_LOW   0x04 	/**< \english 1 - Limit switch connnected to pin SW2 is triggered by a low level on pin. \endenglish \russian 1 - Концевик, подключенный к ножке SW2, считается сработавшим по низкому уровню на контакте. \endrussian */
//@}


/**
	* @anchor flagset_brakeflags
	* \english
	* @name Brake settings flags
	* This is a bit mask for bitwise operations.
	* Specify behaviour of brake.
	* May be combined with bitwise OR.
	* \endenglish
	* \russian
	* @name Флаги настроек тормоза
	* Это битовая маска для побитовых операций.
	* Определяют поведение тормоза.
	* Могут быть объединены с помощью побитового ИЛИ.
	* \endrussian
	* @see get_brake_settings
	* @see set_brake_settings
	* @see brake_settings_t::BrakeFlags, get_brake_settings, set_brake_settings
	*/
//@{
#define BRAKE_ENABLED      0x01 	/**< \english Brake control is enabled, if this flag is set. \endenglish \russian Управление тормозом включено, если флаг установлен. \endrussian */
#define BRAKE_ENG_PWROFF   0x02 	/**< \english Brake turns off power of step motor, if this flag is set. \endenglish \russian Тормоз отключает питание шагового мотора, если флаг установлен. \endrussian */
//@}


/**
	* @anchor flagset_controlflags
	* \english
	* @name Control flags
	* This is a bit mask for bitwise operations.
	* Specify motor control settings by joystick or buttons.
	* May be combined with bitwise OR.
	* \endenglish
	* \russian
	* @name Флаги управления
	* Это битовая маска для побитовых операций.
	* Определяют параметры управления мотором с помощью джойстика или кнопок.
	* Могут быть объединены с помощью побитового ИЛИ.
	* \endrussian
	* @see get_control_settings
	* @see set_control_settings
	* @see control_settings_t::Flags, get_control_settings, set_control_settings
	*/
//@{
#define CONTROL_MODE_BITS               0x03 	/**< \english Bits to control engine by joystick or buttons. \endenglish \russian Биты управления мотором с помощью джойстика или кнопок влево/вправо. \endrussian */
#define CONTROL_MODE_OFF                0x00 	/**< \english Control is disabled. \endenglish \russian Управление отключено. \endrussian */
#define CONTROL_MODE_JOY                0x01 	/**< \english Control by joystick. \endenglish \russian Управление с помощью джойстика. \endrussian */
#define CONTROL_MODE_LR                 0x02 	/**< \english Control by left/right buttons. \endenglish \russian Управление с помощью кнопок влево/вправо. \endrussian */
#define CONTROL_BTN_LEFT_PUSHED_OPEN    0x04 	/**< \english Pushed left button corresponds to open contact, if this flag is set. \endenglish \russian Нажатая левая кнопка соответствует открытому контакту, если этот флаг установлен. \endrussian */
#define CONTROL_BTN_RIGHT_PUSHED_OPEN   0x08 	/**< \english Pushed right button corresponds to open contact, if this flag is set. \endenglish \russian Нажатая правая кнопка соответствует открытому контакту, если этот флаг установлен. \endrussian */
//@}


/**
	* @anchor flagset_joyflags
	* \english
	* @name Joystick flags
	* This is a bit mask for bitwise operations.
	* Control joystick states.
	* \endenglish
	* \russian
	* @name Флаги джойстика
	* Это битовая маска для побитовых операций.
	* Управляют состояниями джойстика.
	* \endrussian
	* @see set_joystick_settings
	* @see get_joystick_settings
	* @see joystick_settings_t::JoyFlags, get_joystick_settings, set_joystick_settings
	*/
//@{
#define JOY_REVERSE   0x01 	/**< \english Joystick action is reversed. Joystick deviation to the upper values correspond to negative speeds and vice versa. \endenglish \russian Реверс воздействия джойстика. Отклонение джойстика к большим значениям приводит к отрицательной скорости и наоборот. \endrussian */
//@}


/**
	* @anchor flagset_ctpflags
	* \english
	* @name Position control flags
	* This is a bit mask for bitwise operations.
	* Specify settings of position control.
	* May be combined with bitwise OR.
	* \endenglish
	* \russian
	* @name Флаги контроля позиции
	* Это битовая маска для побитовых операций.
	* Определяют настройки контроля позиции.
	* Могут быть объединены с помощью побитового ИЛИ.
	* \endrussian
	* @see get_ctp_settings
	* @see set_ctp_settings
	* @see ctp_settings_t::CTPFlags, get_ctp_settings, set_ctp_settings
	*/
//@{
#define CTP_ENABLED            0x01 	/**< \english Position control is enabled, if flag set. \endenglish \russian Контроль позиции включен, если флаг установлен. \endrussian */
#define CTP_BASE               0x02 	/**< \english Position control is based on revolution sensor, if this flag is set; otherwise it is based on encoder. \endenglish \russian Управление положением основано на датчике вращения, если установлен этот флаг; в противном случае - на энкодере. \endrussian */
#define CTP_ALARM_ON_ERROR     0x04 	/**< \english Set ALARM on mismatch, if flag set. \endenglish \russian Войти в состояние ALARM при расхождении позиции, если флаг установлен. \endrussian */
#define REV_SENS_INV           0x08 	/**< \english Sensor is active when it 0 and invert makes active level 1. That is, if you do not invert, it is normal logic - 0 is the activation. \endenglish \russian Сенсор считается активным, когда на нём 0, инвертирование делает активным уровень 1. То есть если не инвертировать, то действует обычная логика - 0 это срабатывание/активация/активное состояние. \endrussian */
#define CTP_ERROR_CORRECTION   0x10 	/**< \english Correct errors which appear when slippage if the flag is set. It works only with the encoder. Incompatible with flag CTP_ALARM_ON_ERROR. \endenglish \russian Корректировать ошибки, возникающие при проскальзывании, если флаг установлен. Работает только с энкодером. Несовместимо с флагом CTP_ALARM_ON_ERROR.\endrussian */
//@}


/**
	* @anchor flagset_homeflags
	* \english
	* @name Home settings flags
	* This is a bit mask for bitwise operations.
	* Specify behaviour for home command.
	* May be combined with bitwise OR.
	* \endenglish
	* \russian
	* @name Флаги настроек команды home
	* Это битовая маска для побитовых операций.
	* Определяют поведение для команды home.
	* Могут быть объединены с помощью побитового ИЛИ.
	* \endrussian
	* @see get_home_settings
	* @see set_home_settings
	* @see command_home
	* @see home_settings_t::HomeFlags, get_home_settings, set_home_settings
	*/
//@{
#define HOME_DIR_FIRST          0x001 	/**< \english Flag defines direction of 1st motion after execution of home command. Direction is right, if set; otherwise left. \endenglish \russian Определяет направление первоначального движения мотора после поступления команды HOME. Если флаг установлен - вправо; иначе - влево. \endrussian */
#define HOME_DIR_SECOND         0x002 	/**< \english Flag defines direction of 2nd motion. Direction is right, if set; otherwise left. \endenglish \russian Определяет направление второго движения мотора. Если флаг установлен - вправо; иначе - влево. \endrussian */
#define HOME_MV_SEC_EN          0x004 	/**< \english Use the second phase of calibration to the home position, if set; otherwise the second phase is skipped. \endenglish \russian Если флаг установлен, реализуется второй этап доводки в домашнюю позицию; иначе - этап пропускается. \endrussian */
#define HOME_HALF_MV            0x008 	/**< \english If the flag is set, the stop signals are ignored in start of second movement the first half-turn. \endenglish \russian Если флаг установлен, в начале второго движения первые пол оборота сигналы завершения движения игнорируются. \endrussian */
#define HOME_STOP_FIRST_BITS    0x030 	/**< \english Bits of the first stop selector. \endenglish \russian Биты, отвечающие за выбор сигнала завершения первого движения. \endrussian */
#define HOME_STOP_FIRST_REV     0x010 	/**< \english First motion stops by  revolution sensor. \endenglish \russian Первое движение завершается по сигналу с Revolution sensor. \endrussian */
#define HOME_STOP_FIRST_SYN     0x020 	/**< \english First motion stops by synchronization input. \endenglish \russian Первое движение завершается по сигналу со входа синхронизации. \endrussian */
#define HOME_STOP_FIRST_LIM     0x030 	/**< \english First motion stops by limit switch. \endenglish \russian Первое движение завершается по сигналу с концевика. \endrussian */
#define HOME_STOP_SECOND_BITS   0x0C0 	/**< \english Bits of the second stop selector. \endenglish \russian Биты, отвечающие за выбор сигнала завершения второго движения. \endrussian */
#define HOME_STOP_SECOND_REV    0x040 	/**< \english Second motion stops by  revolution sensor. \endenglish \russian Второе движение завершается по сигналу с Revolution sensor. \endrussian */
#define HOME_STOP_SECOND_SYN    0x080 	/**< \english Second motion stops by synchronization input. \endenglish \russian Второе движение завершается по сигналу со входа синхронизации. \endrussian */
#define HOME_STOP_SECOND_LIM    0x0C0 	/**< \english Second motion stops by limit switch. \endenglish \russian Второе движение завершается по сигналу с концевика. \endrussian */
#define HOME_USE_FAST           0x100 	/**< \english Use the fast algorithm of calibration to the home position, if set; otherwise the traditional algorithm. \endenglish \russian Если флаг установлен, используется быстрый поиск домашней позиции; иначе - традиционный. \endrussian */
//@}


/**
	* @anchor flagset_uartsetupflags
	* \english
	* @name UART parity flags
	* This is a bit mask for bitwise operations.
	* \endenglish
	* \russian
	* @name Флаги настроек четности команды uart
	* Это битовая маска для побитовых операций.
	* \endrussian
	* @see uart_settings_t::UARTSetupFlags, get_uart_settings, set_uart_settings
	*/
//@{
#define UART_PARITY_BITS        0x03 	/**< \english Bits of the parity. \endenglish \russian Биты, отвечающие за выбор четности. \endrussian */
#define UART_PARITY_BIT_EVEN    0x00 	/**< \english Parity bit 1, if  even \endenglish \russian Бит 1, если четный \endrussian */
#define UART_PARITY_BIT_ODD     0x01 	/**< \english Parity bit 1, if  odd \endenglish \russian Бит 1, если нечетный \endrussian */
#define UART_PARITY_BIT_SPACE   0x02 	/**< \english Parity bit always 0 \endenglish \russian Бит четности всегда 0 \endrussian */
#define UART_PARITY_BIT_MARK    0x03 	/**< \english Parity bit always 1 \endenglish \russian Бит четности всегда 1 \endrussian */
#define UART_PARITY_BIT_USE     0x04 	/**< \english None parity \endenglish \russian Бит чётности не используется, если "0"; бит четности используется, если "1" \endrussian */
#define UART_STOP_BIT           0x08 	/**< \english If set - one stop bit, else two stop bit \endenglish \russian Если установлен, один стоповый бит; иначе - 2 стоповых бита \endrussian */
//@}


/** 
	* @anchor flagset_motortypeflags
 	* \english
	* @name Motor Type flags
	* This is a bit mask for bitwise operations.
	* \endenglish
	* \russian
	* @name Флаги типа двигателя
	* Это битовая маска для побитовых операций.
	* \endrussian
	* @see motor_settings_t::MotorType, get_motor_settings, set_motor_settings
	*/
//@{
#define MOTOR_TYPE_UNKNOWN   0x00 	/**< \english Unknown type of engine \endenglish \russian Неизвестный двигатель \endrussian */
#define MOTOR_TYPE_STEP      0x01 	/**< \english Step engine \endenglish \russian Шаговый двигатель \endrussian */
#define MOTOR_TYPE_DC        0x02 	/**< \english DC engine \endenglish \russian DC двигатель \endrussian */
#define MOTOR_TYPE_BLDC      0x03 	/**< \english BLDC engine \endenglish \russian BLDC двигатель \endrussian */
//@}


/** 
	* @anchor flagset_encodersettingsflags
 	* \english
	* @name Encoder settings flags
	* This is a bit mask for bitwise operations.
	* \endenglish
	* \russian
	* @name Флаги настроек энкодера
	* Это битовая маска для побитовых операций.
	* \endrussian
	* @see encoder_settings_t::EncoderSettings, get_encoder_settings, set_encoder_settings
	*/
//@{
#define ENCSET_DIFFERENTIAL_OUTPUT            0x001 	/**< \english If flag is set the encoder has differential output, else single ended output \endenglish \russian Если флаг установлен, то энкодер имеет дифференциальный выход, иначе - несимметричный выход \endrussian */
#define ENCSET_PUSHPULL_OUTPUT                0x004 	/**< \english If flag is set the encoder has push-pull output, else open drain output \endenglish \russian Если флаг установлен, то энкодер имеет двухтактный выход, иначе - выход с открытым коллектором \endrussian */
#define ENCSET_INDEXCHANNEL_PRESENT           0x010 	/**< \english If flag is set the encoder has index channel, else encoder hasn`t it \endenglish \russian Если флаг установлен, то энкодер имеет дополнительный индексный канал, иначе - он отсутствует \endrussian */
#define ENCSET_REVOLUTIONSENSOR_PRESENT       0x040 	/**< \english If flag is set the encoder has revolution sensor, else encoder hasn`t it \endenglish \russian Если флаг установлен, то энкодер имеет датчик оборотов, иначе - он отсутствует \endrussian */
#define ENCSET_REVOLUTIONSENSOR_ACTIVE_HIGH   0x100 	/**< \english If flag is set the revolution sensor active state is high logic state, else active state is low logic state \endenglish \russian Если флаг установлен, то активное состояние датчика оборотов соответствует логической 1, иначе - логическому 0 \endrussian */
//@}


/** 
	* @anchor flagset_mbsettingsflags
 	* \english
	* @name Magnetic brake settings flags
	* This is a bit mask for bitwise operations.
	* \endenglish
	* \russian
	* @name Флаги настроек энкодера
	* Это битовая маска для побитовых операций.
	* \endrussian
	* @see accessories_settings_t::MBSettings, get_accessories_settings, set_accessories_settings
	*/
//@{
#define MB_AVAILABLE      0x01 	/**< \english If flag is set the magnetic brake is available \endenglish \russian Если флаг установлен, то магнитный тормоз доступен \endrussian */
#define MB_POWERED_HOLD   0x02 	/**< \english If this flag is set the magnetic brake is on when powered \endenglish \russian Если флаг установлен, то магнитный тормоз находится в режиме удержания (активен) при подаче питания \endrussian */
//@}


/** 
	* @anchor flagset_tssettingsflags
 	* \english
	* @name Temperature sensor settings flags
	* This is a bit mask for bitwise operations.
	* \endenglish
	* \russian
	* @name Флаги настроек температурного датчика
	* Это битовая маска для побитовых операций.
	* \endrussian
	* @see accessories_settings_t::TSSettings, get_accessories_settings, set_accessories_settings
	*/
//@{
#define TS_TYPE_BITS            0x07 	/**< \english Bits of the temperature sensor type \endenglish \russian Биты, отвечающие за тип температурного датчика. \endrussian */
#define TS_TYPE_UNKNOWN         0x00 	/**< \english Unknow type of sensor \endenglish \russian Неизвестный сенсор \endrussian */
#define TS_TYPE_THERMOCOUPLE    0x01 	/**< \english Thermocouple \endenglish \russian Термопара \endrussian */
#define TS_TYPE_SEMICONDUCTOR   0x02 	/**< \english The semiconductor temperature sensor \endenglish \russian Полупроводниковый температурный датчик \endrussian */
#define TS_AVAILABLE            0x08 	/**< \english If flag is set the temperature sensor is available \endenglish \russian Если флаг установлен, то датчик температуры доступен \endrussian */
//@}


/** 
	* @anchor flagset_lsflags
 	* \english
	* @name Temperature sensor settings flags
	* This is a bit mask for bitwise operations.
	* \endenglish
	* \russian
	* @name Флаги настроек температурного датчика
	* Это битовая маска для побитовых операций.
	* \endrussian
	* @see accessories_settings_t::LimitSwitchesSettings, get_accessories_settings, set_accessories_settings
	*/
//@{
#define LS_ON_SW1_AVAILABLE   0x01 	/**< \english If flag is set the limit switch connnected to pin SW1 is available \endenglish \russian Если флаг установлен, то концевик, подключенный к ножке SW1, доступен \endrussian */
#define LS_ON_SW2_AVAILABLE   0x02 	/**< \english If flag is set the limit switch connnected to pin SW2 is available \endenglish \russian Если флаг установлен, то концевик, подключенный к ножке SW2, доступен \endrussian */
#define LS_SW1_ACTIVE_LOW     0x04 	/**< \english If flag is set the limit switch connnected to pin SW1 is triggered by a low level on pin \endenglish \russian Если флаг установлен, то концевик, подключенный к ножке SW1, считается сработавшим по низкому уровню на контакте \endrussian */
#define LS_SW2_ACTIVE_LOW     0x08 	/**< \english If flag is set the limit switch connnected to pin SW2 is triggered by a low level on pin \endenglish \russian Если флаг установлен, то концевик, подключенный к ножке SW2, считается сработавшим по низкому уровню на контакте \endrussian */
#define LS_SHORTED            0x10 	/**< \english If flag is set the Limit switches is shorted \endenglish \russian Если флаг установлен, то концевики замкнуты. \endrussian */
//@}


/**
	* @anchor flagset_backemfflags
	* \english
	* @name Flags of auto-detection of characteristics of windings of the engine.
	* This is a bit mask for bitwise operations.
	* \endenglish
	* \russian
	* @name Флаги автоопределения характеристик обмоток двигателя.
	* Это битовая маска для побитовых операций.
	* \endrussian
	* @see set_emf_settings
	* @see get_emf_settings
	* @see emf_settings_t::BackEMFFlags, get_emf_settings, set_emf_settings
	*/
//@{
#define BACK_EMF_INDUCTANCE_AUTO   0x01 	/**< \english Flag of auto-detection of inductance of windings of the engine. \endenglish \russian Флаг автоопределения индуктивности обмоток двигателя. \endrussian */
#define BACK_EMF_RESISTANCE_AUTO   0x02 	/**< \english Flag of auto-detection of resistance of windings of the engine. \endenglish \russian Флаг автоопределения сопротивления обмоток двигателя. \endrussian */
#define BACK_EMF_KM_AUTO           0x04 	/**< \english Flag of auto-detection of electromechanical coefficient of the engine. \endenglish \russian Флаг автоопределения электромеханического коэффициента двигателя. \endrussian */
//@}


/** 
	* \english
	* Feedback settings.
	* This structure contains feedback settings.
	* \endenglish
	* \russian
	* Настройки обратной связи.
	* Эта структура содержит настройки обратной связи.
	* \endrussian
	* @see get_feedback_settings, set_feedback_settings
	*/
	typedef struct
	{
		unsigned int IPS;	/**< \english The number of encoder counts per shaft revolution. Range: 1..655535. The field is obsolete, it is recommended to write 0 to IPS and use the extended CountsPerTurn field. You may need to update the controller firmware to the latest version. \endenglish \russian Количество отсчётов энкодера на оборот вала. Диапазон: 1..65535. Поле устарело, рекомендуется записывать 0 в IPS и использовать расширенное поле CountsPerTurn. Может потребоваться обновление микропрограммы контроллера до последней версии. \endrussian */
		unsigned int FeedbackType;	/**< \english \ref flagset_feedbacktype "Feedback type". \endenglish \russian \ref flagset_feedbacktype "Тип обратной связи". \endrussian */
		unsigned int FeedbackFlags;	/**< \english \ref flagset_feedbackflags "Describes feedback flags". \endenglish \russian \ref flagset_feedbackflags "Флаги обратной связи". \endrussian */
		unsigned int CountsPerTurn;	/**< \english The number of encoder counts per shaft revolution. Range: 1..4294967295. To use the CountsPerTurn field, write 0 in the IPS field, otherwise the value from the IPS field will be used. \endenglish \russian Количество отсчётов энкодера на оборот вала. Диапазон: 1..4294967295. Для использования поля CountsPerTurn нужно записать 0 в поле IPS, иначе будет использоваться значение из поля IPS. \endrussian */
	} feedback_settings_t;

/** 
	* \english
	* Position calibration settings.
	* This structure contains settings used in position calibrating.
	* It specify behaviour of calibrating position.
	* \endenglish
	* \russian
	* Настройки калибровки позиции.
	* Эта структура содержит настройки, использующиеся при калибровке позиции.
	* \endrussian
	* @see get_home_settings
	* @see set_home_settings
	* @see command_home
	* @see get_home_settings, set_home_settings
	*/
	typedef struct
	{
		unsigned int FastHome;	/**< \english Speed used for first motion (full steps). Range: 0..100000. \endenglish \russian Скорость первого движения (в полных шагах). Диапазон: 0..100000 \endrussian */
		unsigned int uFastHome;	/**< \english Part of the speed for first motion, microsteps. Microstep size and the range of valid values for this field depend on selected step division mode (see MicrostepMode field in engine_settings). \endenglish \russian Дробная часть скорости первого движения в микрошагах (используется только с шаговым двигателем). Величина микрошага и диапазон допустимых значений для данного поля зависят от выбранного режима деления шага (см. поле MicrostepMode в engine_settings). \endrussian */
		unsigned int SlowHome;	/**< \english Speed used for second motion (full steps). Range: 0..100000. \endenglish \russian Скорость второго движения (в полных шагах). Диапазон: 0..100000. \endrussian */
		unsigned int uSlowHome;	/**< \english Part of the speed for second motion, microsteps. Microstep size and the range of valid values for this field depend on selected step division mode (see MicrostepMode field in engine_settings). \endenglish \russian Дробная часть скорости второго движения в микрошагах (используется только с шаговым двигателем). Величина микрошага и диапазон допустимых значений для данного поля зависят от выбранного режима деления шага (см. поле MicrostepMode в engine_settings). \endrussian */
		int HomeDelta;	/**< \english Distance from break point (full steps). \endenglish \russian Расстояние отхода от точки останова (в полных шагах). \endrussian */
		int uHomeDelta;	/**< \english Part of the delta distance, microsteps. Microstep size and the range of valid values for this field depend on selected step division mode (see MicrostepMode field in engine_settings). \endenglish \russian Дробная часть расстояния отхода от точки останова в микрошагах (используется только с шаговым двигателем). Величина микрошага и диапазон допустимых значений для данного поля зависят от выбранного режима деления шага (см. поле MicrostepMode в engine_settings). \endrussian */
		unsigned int HomeFlags;	/**< \english \ref flagset_homeflags "Home settings flags". \endenglish \russian \ref flagset_homeflags "Флаги настроек команды home". \endrussian */
	} home_settings_t;

/** 
	* \english
	* Position calibration settings which use user units.
	* This structure contains settings used in position calibrating.
	* It specify behaviour of calibrating position.
	* \endenglish
	* \russian
	* Настройки калибровки позиции с использованием пользовательских единиц.
	* Эта структура содержит настройки, использующиеся при калибровке позиции.
	* \endrussian
	* @see get_home_settings_calb
	* @see set_home_settings_calb
	* @see command_home
	* @see get_home_settings, set_home_settings
	*/
	typedef struct
	{
		float FastHome;	/**< \english Speed used for first motion. \endenglish \russian Скорость первого движения. \endrussian */
		float SlowHome;	/**< \english Speed used for second motion. \endenglish \russian Скорость второго движения. \endrussian */
		float HomeDelta;	/**< \english Distance from break point. \endenglish \russian Расстояние отхода от точки останова. \endrussian */
		unsigned int HomeFlags;	/**< \english \ref flagset_homeflags "Home settings flags". \endenglish \russian \ref flagset_homeflags "Флаги настроек команды home". \endrussian */
	} home_settings_calb_t;

/** 
	* \english
	* Move settings.
	* \endenglish
	* \russian
	* Настройки движения.
	* \endrussian
	* @see set_move_settings
	* @see get_move_settings
	* @see get_move_settings, set_move_settings
	*/
	typedef struct
	{
		unsigned int Speed;	/**< \english Target speed (for stepper motor: steps/s, for DC: rpm). Range: 0..100000. \endenglish \russian Заданная скорость (для ШД: шагов/c, для DC: rpm). Диапазон: 0..100000. \endrussian */
		unsigned int uSpeed;	/**< \english Target speed in microstep fractions/s. Microstep size and the range of valid values for this field depend on selected step division mode (see MicrostepMode field in engine_settings). Using with stepper motor only. \endenglish \russian Заданная скорость в единицах деления микрошага в секунду. Величина микрошага и диапазон допустимых значений для данного поля зависят от выбранного режима деления шага (см. поле MicrostepMode в engine_settings). Используется только с шаговым мотором. \endrussian */
		unsigned int Accel;	/**< \english Motor shaft acceleration, steps/s^2(stepper motor) or RPM/s(DC). Range: 1..65535. \endenglish \russian Ускорение, заданное в шагах в секунду^2(ШД) или в оборотах в минуту за секунду(DC). Диапазон: 1..65535. \endrussian */
		unsigned int Decel;	/**< \english Motor shaft deceleration, steps/s^2(stepper motor) or RPM/s(DC). Range: 1..65535. \endenglish \russian Торможение, заданное в шагах в секунду^2(ШД) или в оборотах в минуту за секунду(DC). Диапазон: 1..65535. \endrussian */
		unsigned int AntiplaySpeed;	/**< \english Speed in antiplay mode, full steps/s(stepper motor) or RPM(DC). Range: 0..100000. \endenglish \russian Скорость в режиме антилюфта, заданная в целых шагах/c(ШД) или в оборотах/с(DC). Диапазон: 0..100000. \endrussian */
		unsigned int uAntiplaySpeed;	/**< \english Speed in antiplay mode, microsteps/s. Microstep size and the range of valid values for this field depend on selected step division mode (see MicrostepMode field in engine_settings). Used with stepper motor only. \endenglish \russian Скорость в режиме антилюфта, выраженная в микрошагах в секунду. Величина микрошага и диапазон допустимых значений для данного поля зависят от выбранного режима деления шага (см. поле MicrostepMode в engine_settings). Используется только с шаговым мотором. \endrussian */
		unsigned int MoveFlags;	/**< \english \ref flagset_moveflags "Flags of the motion parameters". \endenglish \russian \ref flagset_moveflags "Флаги параметров движения". \endrussian */
	} move_settings_t;

/** 
	* \english
	* Move settings which use user units.
	* \endenglish
	* \russian
	* Настройки движения с использованием пользовательских единиц.
	* \endrussian
	* @see set_move_settings_calb
	* @see get_move_settings_calb
	* @see get_move_settings, set_move_settings
	*/
	typedef struct
	{
		float Speed;	/**< \english Target speed. \endenglish \russian Заданная скорость. \endrussian */
		float Accel;	/**< \english Motor shaft acceleration, steps/s^2(stepper motor) or RPM/s(DC). \endenglish \russian Ускорение, заданное в шагах в секунду^2(ШД) или в оборотах в минуту за секунду(DC). \endrussian */
		float Decel;	/**< \english Motor shaft deceleration, steps/s^2(stepper motor) or RPM/s(DC). \endenglish \russian Торможение, заданное в шагах в секунду^2(ШД) или в оборотах в минуту за секунду(DC). \endrussian */
		float AntiplaySpeed;	/**< \english Speed in antiplay mode. \endenglish \russian Скорость в режиме антилюфта. \endrussian */
		unsigned int MoveFlags;	/**< \english \ref flagset_moveflags "Flags of the motion parameters". \endenglish \russian \ref flagset_moveflags "Флаги параметров движения". \endrussian */
	} move_settings_calb_t;

/** 
	* \english
	* Movement limitations and settings, related to the motor.
	* This structure contains useful motor settings.
	* These settings specify motor shaft movement algorithm, list of limitations and rated characteristics.
	* All boards are supplied with standard set of engine setting on controller's flash memory.
	* Please load new engine settings when you change motor, encoder, positioner etc.
	* Please note that wrong engine settings lead to device malfunction, can lead to irreversible damage of board.
	* \endenglish
	* \russian
	* Ограничения и настройки движения, связанные с двигателем.
	* Эта структура содержит настройки мотора.
	* Настройки определяют номинальные значения напряжения, тока, скорости мотора, характер движения и тип мотора.
	* Пожалуйста, загружайте новые настройки когда вы меняете мотор, энкодер или позиционер.
	* Помните, что неправильные настройки мотора могут повредить оборудование.
	* \endrussian
	* @see set_engine_settings
	* @see get_engine_settings
	* @see get_engine_settings, set_engine_settings
	*/
	typedef struct
	{
		unsigned int NomVoltage;	/**< \english Rated voltage in tens of mV. Controller will keep the voltage drop on motor below this value if ENGINE_LIMIT_VOLT flag is set (used with DC only). \endenglish \russian Номинальное напряжение мотора в десятках мВ. Контроллер будет сохранять напряжение на моторе не выше номинального, если установлен флаг ENGINE_LIMIT_VOLT (используется только с DC двигателем). \endrussian */
		unsigned int NomCurrent;	/**< \english Rated current (in mA). Controller will keep current consumed by motor below this value if ENGINE_LIMIT_CURR flag is set. Range: 15..8000 \endenglish \russian Номинальный ток через мотор (в мА). Ток стабилизируется для шаговых и может быть ограничен для DC(если установлен флаг ENGINE_LIMIT_CURR). Диапазон: 15..8000 \endrussian */
		unsigned int NomSpeed;	/**< \english Nominal (maximum) speed (in whole steps/s or rpm for DC and stepper motor as a master encoder). Controller will keep motor shaft RPM below this value if ENGINE_LIMIT_RPM flag is set. Range: 1..100000. \endenglish \russian Номинальная (максимальная) скорость (в целых шагах/с или rpm для DC и шагового двигателя в режиме ведущего энкодера). Контроллер будет сохранять скорость мотора не выше номинальной, если установлен флаг ENGINE_LIMIT_RPM. Диапазон: 1..100000. \endrussian */
		unsigned int uNomSpeed;	/**< \english The fractional part of a nominal speed in microsteps (is only used with stepper motor). Microstep size and the range of valid values for this field depend on selected step division mode (see MicrostepMode field in engine_settings). \endenglish \russian Микрошаговая часть номинальной скорости мотора (используется только с шаговым двигателем). Величина микрошага и диапазон допустимых значений для данного поля зависят от выбранного режима деления шага (см. поле MicrostepMode в engine_settings). \endrussian */
		unsigned int EngineFlags;	/**< \english \ref flagset_engineflags "Flags of engine settings". \endenglish \russian \ref flagset_engineflags "Флаги параметров мотора". \endrussian */
		int Antiplay;	/**< \english Number of pulses or steps for backlash (play) compensation procedure. Used if ENGINE_ANTIPLAY flag is set. \endenglish \russian Количество шагов двигателя или импульсов энкодера, на которое позиционер будет отъезжать от заданной позиции для подхода к ней с одной и той же стороны. Используется, если установлен флаг ENGINE_ANTIPLAY. \endrussian */
		unsigned int MicrostepMode;	/**< \english \ref flagset_microstepmode "Flags of microstep mode". \endenglish \russian \ref flagset_microstepmode "Флаги параметров микрошагового режима". \endrussian */
		unsigned int StepsPerRev;	/**< \english Number of full steps per revolution(Used with stepper motor only). Range: 1..65535. \endenglish \russian Количество полных шагов на оборот(используется только с шаговым двигателем). Диапазон: 1..65535. \endrussian */
	} engine_settings_t;

/** 
	* \english
	* Movement limitations and settings, related to the motor, which use user units.
	* This structure contains useful motor settings.
	* These settings specify motor shaft movement algorithm, list of limitations and rated characteristics.
	* All boards are supplied with standard set of engine setting on controller's flash memory.
	* Please load new engine settings when you change motor, encoder, positioner etc.
	* Please note that wrong engine settings lead to device malfunction, can lead to irreversible damage of board.
	* \endenglish
	* \russian
	* Ограничения и настройки движения, связанные с двигателем, с использованием пользовательских единиц.
	* Эта структура содержит настройки мотора.
	* Настройки определяют номинальные значения напряжения, тока, скорости мотора, характер движения и тип мотора.
	* Пожалуйста, загружайте новые настройки когда вы меняете мотор, энкодер или позиционер.
	* Помните, что неправильные настройки мотора могут повредить оборудование.
	* \endrussian
	* @see set_engine_settings_calb
	* @see get_engine_settings_calb
	* @see get_engine_settings, set_engine_settings
	*/
	typedef struct
	{
		unsigned int NomVoltage;	/**< \english Rated voltage in tens of mV. Controller will keep the voltage drop on motor below this value if ENGINE_LIMIT_VOLT flag is set (used with DC only). \endenglish \russian Номинальное напряжение мотора в десятках мВ. Контроллер будет сохранять напряжение на моторе не выше номинального, если установлен флаг ENGINE_LIMIT_VOLT (используется только с DC двигателем). \endrussian */
		unsigned int NomCurrent;	/**< \english Rated current (in mA). Controller will keep current consumed by motor below this value if ENGINE_LIMIT_CURR flag is set. Range: 15..8000 \endenglish \russian Номинальный ток через мотор (в мА). Ток стабилизируется для шаговых и может быть ограничен для DC(если установлен флаг ENGINE_LIMIT_CURR). Диапазон: 15..8000 \endrussian */
		float NomSpeed;	/**< \english Nominal speed. Controller will keep motor speed below this value if ENGINE_LIMIT_RPM flag is set. \endenglish \russian Номинальная скорость. Контроллер будет сохранять скорость мотора не выше номинальной, если установлен флаг ENGINE_LIMIT_RPM. \endrussian */
		unsigned int EngineFlags;	/**< \english \ref flagset_engineflags "Flags of engine settings". \endenglish \russian \ref flagset_engineflags "Флаги параметров мотора". \endrussian */
		float Antiplay;	/**< \english Number of pulses or steps for backlash (play) compensation procedure. Used if ENGINE_ANTIPLAY flag is set. \endenglish \russian Количество шагов двигателя или импульсов энкодера, на которое позиционер будет отъезжать от заданной позиции для подхода к ней с одной и той же стороны. Используется, если установлен флаг ENGINE_ANTIPLAY. \endrussian */
		unsigned int MicrostepMode;	/**< \english \ref flagset_microstepmode "Flags of microstep mode". \endenglish \russian \ref flagset_microstepmode "Флаги параметров микрошагового режима". \endrussian */
		unsigned int StepsPerRev;	/**< \english Number of full steps per revolution(Used with stepper motor only). Range: 1..65535. \endenglish \russian Количество полных шагов на оборот(используется только с шаговым двигателем). Диапазон: 1..65535. \endrussian */
	} engine_settings_calb_t;

/** 
	* \english
	* Engine type and driver type settings.
	* @param id an identifier of device
	* @param EngineType engine type
	* @param DriverType driver type
	* \endenglish
	* \russian
	* Настройки типа мотора и типа силового драйвера.
	* Эта структура содержит настройки типа мотора и типа силового драйвера.
	* @param id идентификатор устройства
	* @param EngineType тип мотора
	* @param DriverType тип силового драйвера
	* \endrussian
	* @see get_entype_settings, set_entype_settings
	*/
	typedef struct
	{
		unsigned int EngineType;	/**< \english \ref flagset_enginetype "Flags of engine type". \endenglish \russian \ref flagset_enginetype "Флаги, определяющие тип мотора". \endrussian */
		unsigned int DriverType;	/**< \english \ref flagset_drivertype "Flags of driver type". \endenglish \russian \ref flagset_drivertype "Флаги, определяющие тип силового драйвера". \endrussian */
	} entype_settings_t;

/** 
	* \english
	* Step motor power settings.
	* \endenglish
	* \russian
	* Настройки питания шагового мотора.
	* \endrussian
	* @see set_move_settings
	* @see get_move_settings
	* @see get_power_settings, set_power_settings
	*/
	typedef struct
	{
		unsigned int HoldCurrent;	/**< \english Current in holding regime, percent of nominal. Range: 0..100. \endenglish \russian Ток мотора в режиме удержания, в процентах от номинального. Диапазон: 0..100. \endrussian */
		unsigned int CurrReductDelay;	/**< \english Time in ms from going to STOP state to reducting current. \endenglish \russian Время в мс от перехода в состояние STOP до уменьшения тока. \endrussian */
		unsigned int PowerOffDelay;	/**< \english Time in s from going to STOP state to turning power off. \endenglish \russian Время в с от перехода в состояние STOP до отключения питания мотора. \endrussian */
		unsigned int CurrentSetTime;	/**< \english Time in ms to reach nominal current. \endenglish \russian Время в мс, требуемое для набора номинального тока от 0% до 100%. \endrussian */
		unsigned int PowerFlags;	/**< \english \ref flagset_powerflags "Flags of power settings of stepper motor". \endenglish \russian \ref flagset_powerflags "Флаги параметров питания шагового мотора". \endrussian */
	} power_settings_t;

/** 
	* \english
	* This structure contains raw analog data from ADC embedded on board.
	* These data used for device testing and deep recalibraton by manufacturer only.
	* \endenglish
	* \russian
	* Эта структура содержит необработанные данные с АЦП и нормированные значения.
	* Эти данные используются в сервисных целях для тестирования и калибровки устройства.
	* \endrussian
	* @see get_secure_settings
	* @see set_secure_settings
	* @see get_secure_settings, set_secure_settings
	*/
	typedef struct
	{
		unsigned int LowUpwrOff;	/**< \english Lower voltage limit to turn off the motor, tens of mV. \endenglish \russian Нижний порог напряжения на силовой части для выключения, десятки мВ. \endrussian */
		unsigned int CriticalIpwr;	/**< \english Maximum motor current which triggers ALARM state, in mA. \endenglish \russian Максимальный ток силовой части, вызывающий состояние ALARM, в мА. \endrussian */
		unsigned int CriticalUpwr;	/**< \english Maximum motor voltage which triggers ALARM state, tens of mV. \endenglish \russian Максимальное напряжение на силовой части, вызывающее состояние ALARM, десятки мВ. \endrussian */
		unsigned int CriticalT;	/**< \english Maximum temperature, which triggers ALARM state, in tenths of degrees Celcius. \endenglish \russian Максимальная температура контроллера, вызывающая состояние ALARM, в десятых долях градуса Цельсия.\endrussian */
		unsigned int CriticalIusb;	/**< \english Maximum USB current which triggers ALARM state, in mA. \endenglish \russian Максимальный ток USB, вызывающий состояние ALARM, в мА. \endrussian */
		unsigned int CriticalUusb;	/**< \english Maximum USB voltage which triggers ALARM state, tens of mV. \endenglish \russian Максимальное напряжение на USB, вызывающее состояние ALARM, десятки мВ. \endrussian */
		unsigned int MinimumUusb;	/**< \english Minimum USB voltage which triggers ALARM state, tens of mV. \endenglish \russian Минимальное напряжение на USB, вызывающее состояние ALARM, десятки мВ. \endrussian */
		unsigned int Flags;	/**< \english \ref flagset_secureflags "Flags of secure settings". \endenglish \russian \ref flagset_secureflags "Флаги критических параметров". \endrussian */
	} secure_settings_t;

/**  
	* \english
	* Edges settings.
	* This structure contains border and limit switches settings.
	* Please load new engine settings when you change positioner etc.
	* Please note that wrong engine settings lead to device malfunction, can lead to irreversible damage of board.
	* \endenglish
	* \russian
	* Настройки границ.
	* Эта структура содержит настройки границ и концевых выключателей.
	* Пожалуйста, загружайте новые настройки когда вы меняете позиционер.
	* Помните, что неправильные настройки мотора могут повредить оборудование.
	* \endrussian
	* @see set_edges_settings
	* @see get_edges_settings
	* @see get_edges_settings, set_edges_settings
	*/
	typedef struct
	{
		unsigned int BorderFlags;	/**< \english \ref flagset_borderflags "Border flags". \endenglish \russian \ref flagset_borderflags "Флаги границ". \endrussian */
		unsigned int EnderFlags;	/**< \english \ref flagset_enderflags "Limit switches flags". \endenglish \russian \ref flagset_enderflags "Флаги концевых выключателей". \endrussian */
		int LeftBorder;	/**< \english Left border position, used if BORDER_IS_ENCODER flag is set. \endenglish \russian Позиция левой границы, используется если установлен флаг BORDER_IS_ENCODER. \endrussian */
		int uLeftBorder;	/**< \english Left border position in microsteps(used with stepper motor only). Microstep size and the range of valid values for this field depend on selected step division mode (see MicrostepMode field in engine_settings). \endenglish \russian Позиция левой границы в микрошагах (используется только с шаговым двигателем). Величина микрошага и диапазон допустимых значений для данного поля зависят от выбранного режима деления шага (см. поле MicrostepMode в engine_settings). \endrussian */
		int RightBorder;	/**< \english Right border position, used if BORDER_IS_ENCODER flag is set. \endenglish \russian Позиция правой границы, используется если установлен флаг BORDER_IS_ENCODER. \endrussian */
		int uRightBorder;	/**< \english Right border position in microsteps. Used with stepper motor only. Microstep size and the range of valid values for this field depend on selected step division mode (see MicrostepMode field in engine_settings). \endenglish \russian Позиция правой границы в микрошагах (используется только с шаговым двигателем). Величина микрошага и диапазон допустимых значений для данного поля зависят от выбранного режима деления шага (см. поле MicrostepMode в engine_settings). \endrussian */
	} edges_settings_t;

/**  
	* \english
	* Edges settings which use user units.
	* This structure contains border and limit switches settings.
	* Please load new engine settings when you change positioner etc.
	* Please note that wrong engine settings lead to device malfunction, can lead to irreversible damage of board.
	* \endenglish
	* \russian
	* Настройки границ с использованием пользовательских единиц.
	* Эта структура содержит настройки границ и концевых выключателей.
	* Пожалуйста, загружайте новые настройки когда вы меняете позиционер.
	* Помните, что неправильные настройки мотора могут повредить оборудование.
	* \endrussian
	* @see set_edges_settings_calb
	* @see get_edges_settings_calb
	* @see get_edges_settings, set_edges_settings
	*/
	typedef struct
	{
		unsigned int BorderFlags;	/**< \english \ref flagset_borderflags "Border flags". \endenglish \russian \ref flagset_borderflags "Флаги границ". \endrussian */
		unsigned int EnderFlags;	/**< \english \ref flagset_enderflags "Limit switches flags". \endenglish \russian \ref flagset_enderflags "Флаги концевых выключателей". \endrussian */
		float LeftBorder;	/**< \english Left border position, used if BORDER_IS_ENCODER flag is set. Corrected by the table. \endenglish \russian Позиция левой границы, используется если установлен флаг BORDER_IS_ENCODER. Корректируется таблицей. \endrussian */
		float RightBorder;	/**< \english Right border position, used if BORDER_IS_ENCODER flag is set. Corrected by the table. \endenglish \russian Позиция правой границы, используется если установлен флаг BORDER_IS_ENCODER. Корректируется таблицей. \endrussian */
	} edges_settings_calb_t;

/**  
	* \english
	* PID settings.
	* This structure contains factors for PID routine.
	* It specify behaviour of PID routine for voltage.
	* These factors are slightly different for different positioners.
	* All boards are supplied with standard set of PID setting on controller's flash memory.
	* Please load new PID settings when you change positioner.
	* Please note that wrong PID settings lead to device malfunction.
	* \endenglish
	* \russian
	* Настройки ПИД.
	* Эта структура содержит коэффициенты для ПИД регулятора.
	* Они определяют работу ПИД контура напряжения.
	* Эти коэффициенты хранятся во flash памяти памяти контроллера.
	* Пожалуйста, загружайте новые настройки, когда вы меняете мотор или позиционер.
	* Помните, что неправильные настройки ПИД контуров могут повредить оборудование.
	* \endrussian

	* @see set_pid_settings
	* @see get_pid_settings
	* @see get_pid_settings, set_pid_settings
	*/
	typedef struct
	{
		unsigned int KpU;	/**< \english Proportional gain for voltage PID routine \endenglish \russian Пропорциональный коэффициент ПИД контура по напряжению \endrussian */
		unsigned int KiU;	/**< \english Integral gain for voltage PID routine \endenglish \russian Интегральный коэффициент ПИД контура по напряжению \endrussian */
		unsigned int KdU;	/**< \english Differential gain for voltage PID routine \endenglish \russian Дифференциальный коэффициент ПИД контура по напряжению \endrussian */
		float Kpf;	/**< \english Proportional gain for BLDC position PID routine \endenglish \russian Пропорциональный коэффициент ПИД контура по позиции для BLDC \endrussian */
		float Kif;	/**< \english Integral gain for BLDC position PID routine \endenglish \russian Интегральный коэффициент ПИД контура по позиции для BLDC \endrussian */
		float Kdf;	/**< \english Differential gain for BLDC position PID routine \endenglish \russian Дифференциальный коэффициент ПИД контура по позиции для BLDC \endrussian */
	} pid_settings_t;

/** 
	* \english
	* Synchronization settings.
	* This structure contains all synchronization settings, modes, periods and flags.
	* It specifes behaviour of input synchronization.
	* All boards are supplied with standard set of these settings.
	* \endenglish
	* \russian
	* Настройки входной синхронизации.
	* Эта структура содержит все настройки, определяющие поведение входа синхронизации.
	* \endrussian
	* @see get_sync_in_settings
	* @see set_sync_in_settings
	* @see get_sync_in_settings, set_sync_in_settings
	*/
	typedef struct
	{
		unsigned int SyncInFlags;	/**< \english \ref flagset_syncinflags "Flags for synchronization input setup". \endenglish \russian \ref flagset_syncinflags "Флаги настроек синхронизации входа". \endrussian */
		unsigned int ClutterTime;	/**< \english Input synchronization pulse dead time (mks). \endenglish \russian Минимальная длительность входного импульса синхронизации для защиты от дребезга (мкс). \endrussian */
		int Position;	/**< \english Desired position or shift (full steps) \endenglish \russian Желаемая позиция или смещение (в полных шагах) \endrussian */
		int uPosition;	/**< \english The fractional part of a position or shift in microsteps. Is used with stepper motor. Microstep size and the range of valid values for this field depend on selected step division mode (see MicrostepMode field in engine_settings). \endenglish \russian Дробная часть позиции или смещения в микрошагах. Используется только с шаговым двигателем. Величина микрошага и диапазон допустимых значений для данного поля зависят от выбранного режима деления шага (см. поле MicrostepMode в engine_settings). \endrussian */
		unsigned int Speed;	/**< \english Target speed (for stepper motor: steps/s, for DC: rpm). Range: 0..100000. \endenglish \russian Заданная скорость (для ШД: шагов/c, для DC: rpm). Диапазон: 0..100000. \endrussian */
		unsigned int uSpeed;	/**< \english Target speed in microsteps/s. Microstep size and the range of valid values for this field depend on selected step division mode (see MicrostepMode field in engine_settings). Using with stepper motor only. \endenglish \russian Заданная скорость в микрошагах в секунду. Величина микрошага и диапазон допустимых значений для данного поля зависят от выбранного режима деления шага (см. поле MicrostepMode в engine_settings). Используется только с шаговым мотором. \endrussian */
	} sync_in_settings_t;

/** 
	* \english
	* Synchronization settings which use user units.
	* This structure contains all synchronization settings, modes, periods and flags.
	* It specifes behaviour of input synchronization.
	* All boards are supplied with standard set of these settings.
	* \endenglish
	* \russian
	* Настройки входной синхронизации с использованием пользовательских единиц.
	* Эта структура содержит все настройки, определяющие поведение входа синхронизации.
	* \endrussian
	* @see get_sync_in_settings_calb
	* @see set_sync_in_settings_calb
	* @see get_sync_in_settings, set_sync_in_settings
	*/
	typedef struct
	{
		unsigned int SyncInFlags;	/**< \english \ref flagset_syncinflags "Flags for synchronization input setup". \endenglish \russian \ref flagset_syncinflags "Флаги настроек синхронизации входа". \endrussian */
		unsigned int ClutterTime;	/**< \english Input synchronization pulse dead time (mks). \endenglish \russian Минимальная длительность входного импульса синхронизации для защиты от дребезга (мкс). \endrussian */
		float Position;	/**< \english Desired position or shift. \endenglish \russian Желаемая позиция или смещение. \endrussian */
		float Speed;	/**< \english Target speed. \endenglish \russian Заданная скорость. \endrussian */
	} sync_in_settings_calb_t;

/** 
	* \english
	* Synchronization settings.
	* This structure contains all synchronization settings, modes, periods and flags.
	* It specifes behaviour of output synchronization.
	* All boards are supplied with standard set of these settings.
	* \endenglish
	* \russian
	* Настройки выходной синхронизации.
	* Эта структура содержит все настройки, определяющие поведение выхода синхронизации.
	* \endrussian
	* @see get_sync_out_settings
	* @see set_sync_out_settings
	* @see get_sync_out_settings, set_sync_out_settings
	*/
	typedef struct
	{
		unsigned int SyncOutFlags;	/**< \english \ref flagset_syncoutflags "Flags of synchronization output". \endenglish \russian \ref flagset_syncoutflags "Флаги настроек синхронизации выхода". \endrussian */
		unsigned int SyncOutPulseSteps;	/**< \english This value specifies duration of output pulse. It is measured microseconds when SYNCOUT_IN_STEPS flag is cleared or in encoder pulses or motor steps when SYNCOUT_IN_STEPS is set. \endenglish \russian Определяет длительность выходных импульсов в шагах/импульсах энкодера, когда установлен флаг SYNCOUT_IN_STEPS, или в микросекундах если флаг сброшен. \endrussian */
		unsigned int SyncOutPeriod;	/**< \english This value specifies number of encoder pulses or steps between two output synchronization pulses when SYNCOUT_ONPERIOD is set. \endenglish \russian Период генерации импульсов (в шагах/отсчетах энкодера), используется при установленном флаге SYNCOUT_ONPERIOD. \endrussian */
		unsigned int Accuracy;	/**< \english This is the neighborhood around the target coordinates, which is getting hit in the target position and the momentum generated by the stop. \endenglish \russian Это окрестность вокруг целевой координаты, попадание в которую считается попаданием в целевую позицию и генерируется импульс по остановке. \endrussian */
		unsigned int uAccuracy;	/**< \english This is the neighborhood around the target coordinates in microsteps (only used with stepper motor). Microstep size and the range of valid values for this field depend on selected step division mode (see MicrostepMode field in engine_settings). \endenglish \russian Это окрестность вокруг целевой координаты в микрошагах (используется только с шаговым двигателем). Величина микрошага и диапазон допустимых значений для данного поля зависят от выбранного режима деления шага (см. поле MicrostepMode в engine_settings). \endrussian */
	} sync_out_settings_t;

/** 
	* \english
	* Synchronization settings which use user units.
	* This structure contains all synchronization settings, modes, periods and flags.
	* It specifes behaviour of output synchronization.
	* All boards are supplied with standard set of these settings.
	* \endenglish
	* \russian
	* Настройки выходной синхронизации с использованием пользовательских единиц.
	* Эта структура содержит все настройки, определяющие поведение выхода синхронизации.
	* \endrussian
	* @see get_sync_out_settings_calb
	* @see set_sync_out_settings_calb
	* @see get_sync_out_settings, set_sync_out_settings
	*/
	typedef struct
	{
		unsigned int SyncOutFlags;	/**< \english \ref flagset_syncoutflags "Flags of synchronization output". \endenglish \russian \ref flagset_syncoutflags "Флаги настроек синхронизации выхода". \endrussian */
		unsigned int SyncOutPulseSteps;	/**< \english This value specifies duration of output pulse. It is measured microseconds when SYNCOUT_IN_STEPS flag is cleared or in encoder pulses or motor steps when SYNCOUT_IN_STEPS is set. \endenglish \russian Определяет длительность выходных импульсов в шагах/импульсах энкодера, когда установлен флаг SYNCOUT_IN_STEPS, или в микросекундах если флаг сброшен. \endrussian */
		unsigned int SyncOutPeriod;	/**< \english This value specifies number of encoder pulses or steps between two output synchronization pulses when SYNCOUT_ONPERIOD is set. \endenglish \russian Период генерации импульсов (в шагах/отсчетах энкодера), используется при установленном флаге SYNCOUT_ONPERIOD. \endrussian */
		float Accuracy;	/**< \english This is the neighborhood around the target coordinates (in encoder pulses or motor steps), which is getting hit in the target position and the momentum generated by the stop. \endenglish \russian Это окрестность вокруг целевой координаты (в шагах/отсчетах энкодера), попадание в которую считается попаданием в целевую позицию и генерируется импульс по остановке. \endrussian */
	} sync_out_settings_calb_t;

/** 
	* \english
	* EXTIO settings.
	* This structure contains all EXTIO settings.
	* By default input event are signalled through rising front and output states are signalled by high logic state.
	* \endenglish
	* \russian
	* Настройки EXTIO.
	* Эта структура содержит все настройки, определяющие поведение ножки EXTIO.
	* Входные события обрабатываются по фронту. Выходные состояния сигнализируются логическим состоянием.
	* По умолчанию нарастающий фронт считается моментом подачи входного сигнала, а единичное состояние считается активным выходом.
	* \endrussian
	* @see get_extio_settings
	* @see set_extio_settings
	* @see get_extio_settings, set_extio_settings
	*/
	typedef struct
	{
		unsigned int EXTIOSetupFlags;	/**< \english \ref flagset_extiosetupflags "External IO setup flags". \endenglish \russian \ref flagset_extiosetupflags "Флаги настройки работы внешнего ввода/вывода". \endrussian */
		unsigned int EXTIOModeFlags;	/**< \english \ref flagset_extiomodeflags "External IO mode flags". \endenglish \russian \ref flagset_extiomodeflags "Флаги настройки режимов внешнего ввода/вывода". \endrussian */
	} extio_settings_t;

/** 
	* \english
	* Brake settings.
	* This structure contains parameters of brake control.
	* \endenglish
	* \russian
	* Настройки тормоза.
	* Эта структура содержит параметры управления тормозом.
	* \endrussian
	* @see set_brake_settings
	* @see get_brake_settings
	* @see get_brake_settings, set_brake_settings
	*/
	typedef struct
	{
		unsigned int t1;	/**< \english Time in ms between turn on motor power and turn off brake. \endenglish \russian Время в мс между включением питания мотора и отключением тормоза. \endrussian */
		unsigned int t2;	/**< \english Time in ms between turn off brake and moving readiness. All moving commands will execute after this interval. \endenglish \russian Время в мс между отключением тормоза и готовностью к движению. Все команды движения начинают выполняться только по истечении этого времени. \endrussian */
		unsigned int t3;	/**< \english Time in ms between motor stop and turn on brake. \endenglish \russian Время в мс между остановкой мотора и включением тормоза. \endrussian */
		unsigned int t4;	/**< \english Time in ms between turn on brake and turn off motor power. \endenglish \russian Время в мс между включением тормоза и отключением питания мотора. \endrussian */
		unsigned int BrakeFlags;	/**< \english \ref flagset_brakeflags "Brake settings flags". \endenglish \russian \ref flagset_brakeflags "Флаги настроек тормоза". \endrussian */
	} brake_settings_t;

/** 
	* \english
	* Control settings.
	* This structure contains control parameters.
	* When choosing CTL_MODE=1 switches motor control with the joystick.
	* In this mode, the joystick to the maximum engine tends
	* Move at MaxSpeed [i], where i=0 if the previous use
	* This mode is not selected another i. Buttons switch the room rate i.
	* When CTL_MODE=2 is switched on motor control using the
	* Left / right. When you click on the button motor starts to move in the appropriate direction at a speed MaxSpeed [0],
	* at the end of time Timeout[i] motor move at a speed MaxSpeed [i+1]. at
	* Transition from MaxSpeed [i] on MaxSpeed [i+1] to acceleration, as usual.
	* The figure above shows the sensitivity of the joystick feature on its position.
	* \endenglish
	* \russian
	* Настройки управления.
	* При выборе CTL_MODE=1 включается управление мотором с помощью джойстика.
	* В этом режиме при отклонении джойстика на максимум двигатель стремится
	* двигаться со скоростью MaxSpeed [i], где i=0, если предыдущим использованием
	* этого режима не было выбрано другое i. Кнопки переключают номер скорости i.
	* При выборе CTL_MODE=2 включается управление мотором с помощью кнопок
	* left/right. При нажатии на кнопки двигатель начинает двигаться в соответствующую сторону со скоростью MaxSpeed [0], по истечении времени Timeout[i] мотор
	* двигается со скоростью MaxSpeed [i+1]. При
	* переходе от MaxSpeed [i] на MaxSpeed [i+1] действует ускорение, как обычно.
	* \endrussian
	* @see set_control_settings
	* @see get_control_settings
	* @see get_control_settings, set_control_settings
	*/
	typedef struct
	{
		unsigned int MaxSpeed[10];	/**< \english Array of speeds (full step) using with joystick and button control. Range: 0..100000. \endenglish \russian Массив скоростей (в полных шагах), использующийся при управлении джойстиком или кнопками влево/вправо. Диапазон: 0..100000. \endrussian */
		unsigned int uMaxSpeed[10];	/**< \english Array of speeds (in microsteps) using with joystick and button control. Microstep size and the range of valid values for this field depend on selected step division mode (see MicrostepMode field in engine_settings). \endenglish \russian Массив скоростей (в микрошагах), использующийся при управлении джойстиком или кнопками влево/вправо. Величина микрошага и диапазон допустимых значений для данного поля зависят от выбранного режима деления шага (см. поле MicrostepMode в engine_settings). \endrussian */
		unsigned int Timeout[9];	/**< \english timeout[i] is time in ms, after that max_speed[i+1] is applying. It is using with buttons control only. \endenglish \russian timeout[i] - время в мс, по истечении которого устанавливается скорость max_speed[i+1] (используется только при управлении кнопками). \endrussian */
		unsigned int MaxClickTime;	/**< \english Maximum click time (in ms). Prior to the expiration of this time the first speed isn't enabled. \endenglish \russian Максимальное время клика (в мс). До истечения этого времени первая скорость не включается. \endrussian */
		unsigned int Flags;	/**< \english \ref flagset_controlflags "Control flags". \endenglish \russian \ref flagset_controlflags "Флаги управления". \endrussian */
		int DeltaPosition;	/**< \english Shift (delta) of position (full step) \endenglish \russian Смещение (дельта) позиции (в полных шагах) \endrussian */
		int uDeltaPosition;	/**< \english Fractional part of the shift in micro steps. Is only used with stepper motor. Microstep size and the range of valid values for this field depend on selected step division mode (see MicrostepMode field in engine_settings). \endenglish \russian Дробная часть смещения в микрошагах. Используется только с шаговым двигателем. Величина микрошага и диапазон допустимых значений для данного поля зависят от выбранного режима деления шага (см. поле MicrostepMode в engine_settings). \endrussian */
	} control_settings_t;

/** 
	* \english
	* Control settings which use user units.
	* This structure contains control parameters.
	* When choosing CTL_MODE=1 switches motor control with the joystick.
	* In this mode, the joystick to the maximum engine tends
	* Move at MaxSpeed [i], where i=0 if the previous use
	* This mode is not selected another i. Buttons switch the room rate i.
	* When CTL_MODE=2 is switched on motor control using the
	* Left / right. When you click on the button motor starts to move in the appropriate direction at a speed MaxSpeed [0],
	* at the end of time Timeout[i] motor move at a speed MaxSpeed [i+1]. at
	* Transition from MaxSpeed [i] on MaxSpeed [i+1] to acceleration, as usual.
	* The figure above shows the sensitivity of the joystick feature on its position.
	* \endenglish
	* \russian
	* Настройки управления с использованием пользовательских единиц.
	* При выборе CTL_MODE=1 включается управление мотором с помощью джойстика.
	* В этом режиме при отклонении джойстика на максимум двигатель стремится
	* двигаться со скоростью MaxSpeed [i], где i=0, если предыдущим использованием
	* этого режима не было выбрано другое i. Кнопки переключают номер скорости i.
	* При выборе CTL_MODE=2 включается управление мотором с помощью кнопок
	* left/right. При нажатии на кнопки двигатель начинает двигаться в соответствующую сторону со скоростью MaxSpeed [0], по истечении времени Timeout[i] мотор
	* двигается со скоростью MaxSpeed [i+1]. При
	* переходе от MaxSpeed [i] на MaxSpeed [i+1] действует ускорение, как обычно.
	* \endrussian
	* @see set_control_settings_calb
	* @see get_control_settings_calb
	* @see get_control_settings, set_control_settings
	*/
	typedef struct
	{
		float MaxSpeed[10];	/**< \english Array of speeds using with joystick and button control. \endenglish \russian Массив скоростей, использующийся при управлении джойстиком или кнопками влево/вправо. \endrussian */
		unsigned int Timeout[9];	/**< \english timeout[i] is time in ms, after that max_speed[i+1] is applying. It is using with buttons control only. \endenglish \russian timeout[i] - время в мс, по истечении которого устанавливается скорость max_speed[i+1] (используется только при управлении кнопками). \endrussian */
		unsigned int MaxClickTime;	/**< \english Maximum click time (in ms). Prior to the expiration of this time the first speed isn't enabled. \endenglish \russian Максимальное время клика (в мс). До истечения этого времени первая скорость не включается. \endrussian */
		unsigned int Flags;	/**< \english \ref flagset_controlflags "Control flags". \endenglish \russian \ref flagset_controlflags "Флаги управления". \endrussian */
		float DeltaPosition;	/**< \english Shift (delta) of position \endenglish \russian Смещение (дельта) позиции \endrussian */
	} control_settings_calb_t;

/** 
	* \english
	* Joystick settings.
	* This structure contains joystick parameters.
	* If joystick position is outside DeadZone limits from the central position a movement with speed,
	* defined by the joystick DeadZone edge to 100% deviation, begins. Joystick positions inside DeadZone limits
	* correspond to zero speed (soft stop of motion) and positions beyond Low and High limits correspond MaxSpeed [i]
	* or -MaxSpeed [i] (see command SCTL), where i = 0 by default and can be changed with left/right buttons (see command SCTL).
	* If next speed in list is zero (both integer and microstep parts), the button press is ignored. First speed in list shouldn't be zero.
	* The relationship between the deviation and the rate is exponential,
	* allowing no switching speed combine high mobility and accuracy.
	* \endenglish
	* \russian
	* Настройки джойстика.
	* Команда чтения настроек и калибровки джойстика.
	* При отклонении джойстика более чем на DeadZone от центрального положения начинается движение со скоростью,
	* определяемой отклонением джойстика от DeadZone до 100% отклонения, причем отклонению DeadZone соответствует
	* нулевая скорость, а 100% отклонения соответствует MaxSpeed [i] (см. команду SCTL), где i=0, если предыдущим
	* использованием этого режима не было выбрано другое i.
	* Если следующая скорость в таблице скоростей нулевая (целая и микрошаговая части), то перехода на неё не происходит.
	* DeadZone вычисляется в десятых долях процента отклонения
	* от центра (JoyCenter) до правого или левого максимума. Зависимость между отклонением и скоростью экспоненциальная,
	* что позволяет без переключения режимов скорости сочетать высокую подвижность и точность.
	* \endrussian
	* @see set_joystick_settings
	* @see get_joystick_settings
	* @see get_joystick_settings, set_joystick_settings
	*/
	typedef struct
	{
		unsigned int JoyLowEnd;	/**< \english Joystick lower end position. Range: 0..10000. \endenglish \russian Значение в шагах джойстика, соответствующее нижней границе диапазона отклонения устройства. Должно лежать в пределах. Диапазон: 0..10000. \endrussian */
		unsigned int JoyCenter;	/**< \english Joystick center position. Range: 0..10000. \endenglish \russian Значение в шагах джойстика, соответствующее неотклонённому устройству. Должно лежать в пределах. Диапазон: 0..10000. \endrussian */
		unsigned int JoyHighEnd;	/**< \english Joystick higher end position. Range: 0..10000. \endenglish \russian Значение в шагах джойстика, соответствующее верхней границе диапазона отклонения устройства. Должно лежать в пределах. Диапазон: 0..10000. \endrussian */
		unsigned int ExpFactor;	/**< \english Exponential nonlinearity factor. \endenglish \russian Фактор экспоненциальной нелинейности отклика джойстика. \endrussian */
		unsigned int DeadZone;	/**< \english Joystick dead zone. \endenglish \russian Отклонение от среднего положения, которое не вызывает начала движения (в десятых долях процента). Максимальное мёртвое отклонение +-25.5%, что составляет половину рабочего диапазона джойстика. \endrussian */
		unsigned int JoyFlags;	/**< \english \ref flagset_joyflags "Joystick flags". \endenglish \russian \ref flagset_joyflags "Флаги джойстика". \endrussian */
	} joystick_settings_t;

/** 
	* \english
	* Control position settings(is only used with stepper motor).
	* When controlling the step motor with encoder (CTP_BASE 0) it is possible
	* to detect the loss of steps. The controller knows the number of steps per
	* revolution (GENG :: StepsPerRev) and the encoder resolution (GFBS :: IPT).
	* When the control (flag CTP_ENABLED), the controller stores the current position
	* in the footsteps of SM and the current position of the encoder. Further, at
	* each step of the position encoder is converted into steps and if the difference
	* is greater CTPMinError, a flag STATE_CTP_ERROR and set ALARM state.
	* When controlling the step motor with speed sensor (CTP_BASE 1), the position is
	* controlled by him. The active edge of input clock controller stores the current
	* value of steps. Further, at each turn checks how many steps shifted. When a
	* mismatch CTPMinError a flag STATE_CTP_ERROR and set ALARM state.
	* \endenglish
	* \russian
	* Настройки контроля позиции(для шагового двигателя).
	* При управлении ШД с энкодером
	* (CTP_BASE 0) появляется возможность обнаруживать потерю шагов. Контроллер
	* знает кол-во шагов на оборот (GENG::StepsPerRev) и разрешение энкодера
	* (GFBS::IPT). При включении контроля (флаг CTP_ENABLED), контроллер запоминает
	* текущую позицию в шагах ШД и текущую позицию энкодера. Далее, на каждом шаге
	* позиция энкодера преобразовывается в шаги и если разница оказывается больше
	* CTPMinError, устанавливается флаг STATE_CTP_ERROR и устанавливается состояние ALARM.
	* При управлении ШД с датчиком оборотов (CTP_BASE 1), позиция контролируется по нему.
	* По активному фронту на входе синхронизации контроллер запоминает текущее значение
	* шагов. Далее, при каждом обороте проверяет, на сколько шагов сместились. При
	* рассогласовании более CTPMinError устанавливается флаг STATE_CTP_ERROR и устанавливается состояние ALARM.
	* \endrussian
	* @see set_ctp_settings
	* @see get_ctp_settings
	* @see get_ctp_settings, set_ctp_settings
	*/
	typedef struct
	{
		unsigned int CTPMinError;	/**< \english Minimum contrast steps from step motor encoder position, wich set STATE_CTP_ERROR flag. Measured in steps step motor. \endenglish \russian Минимальное отличие шагов ШД от положения энкодера, устанавливающее флаг STATE_RT_ERROR. Измеряется в шагах ШД. \endrussian */
		unsigned int CTPFlags;	/**< \english \ref flagset_ctpflags "Position control flags". \endenglish \russian \ref flagset_ctpflags "Флаги контроля позиции". \endrussian */
	} ctp_settings_t;

/** 
	* \english
	* UART settings.
	* This structure contains UART settings.
	* \endenglish
	* \russian
	* Настройки UART.
	* Эта структура содержит настройки UART.
	* \endrussian
	* @see get_uart_settings
	* @see set_uart_settings
	* @see get_uart_settings, set_uart_settings
	*/
	typedef struct
	{
		unsigned int Speed;	/**< \english UART speed (in bauds) \endenglish \russian Cкорость UART (в бодах) \endrussian */
		unsigned int UARTSetupFlags;	/**< \english \ref flagset_uartsetupflags "UART parity flags". \endenglish \russian \ref flagset_uartsetupflags "Флаги настроек четности команды uart". \endrussian */
	} uart_settings_t;

/** 
	* \english
	* Calibration settings.
	* This structure contains calibration settings.
	* \endenglish
	* \russian
	* Калибровочные коэффициенты.
	* Эта структура содержит калибровочные коэффициенты.
	* \endrussian
	* @see get_calibration_settings
	* @see set_calibration_settings
	* @see get_calibration_settings, set_calibration_settings
	*/
	typedef struct
	{
		float CSS1_A;	/**< \english Scaling factor for the analogue measurements of the winding A current. \endenglish \russian Коэффициент масштабирования для аналоговых измерений тока в обмотке A. \endrussian */
		float CSS1_B;	/**< \english Shift factor for the analogue measurements of the winding A current. \endenglish \russian Коэффициент сдвига для аналоговых измерений тока в обмотке A. \endrussian */
		float CSS2_A;	/**< \english Scaling factor for the analogue measurements of the winding B current. \endenglish \russian Коэффициент масштабирования для аналоговых измерений тока в обмотке B. \endrussian */
		float CSS2_B;	/**< \english Shift factor for the analogue measurements of the winding B current. \endenglish \russian Коэффициент сдвига для аналоговых измерений тока в обмотке B. \endrussian */
		float FullCurrent_A;	/**< \english Scaling factor for the analogue measurements of the full current. \endenglish \russian Коэффициент масштабирования для аналоговых измерений полного тока. \endrussian */
		float FullCurrent_B;	/**< \english Shift factor for the analogue measurements of the full current. \endenglish \russian Коэффициент сдвига для аналоговых измерений полного тока. \endrussian */
	} calibration_settings_t;

/** 
	* \english
	* Controller user name and flags of setting.
	* \endenglish
	* \russian
	* Пользовательское имя контроллера и флаги настройки.
	* \endrussian
	* @see get_controller_name, set_controller_name
	*/
	typedef struct
	{
		char ControllerName[17];	/**< \english User conroller name. Can be set by user for his/her convinience. Max string length: 16 chars. \endenglish \russian Пользовательское имя контроллера. Может быть установлено пользователем для его удобства. Максимальная длина строки: 16 символов. \endrussian */
		unsigned int CtrlFlags;	/**< \english \ref flagset_controllerflags "Flags of internal controller settings". \endenglish \russian \ref flagset_controllerflags "Флаги настроек контроллера". \endrussian */
	} controller_name_t;

/** 
	* \english
	* Userdata for save into FRAM.
	* \endenglish
	* \russian
	* Пользовательские данные для сохранения во FRAM.
	* \endrussian
	* @see get_nonvolatile_memory, set_nonvolatile_memory
	*/
	typedef struct
	{
		unsigned int UserData[7];	/**< \english User data. Can be set by user for his/her convinience. Each element of the array stores only 32 bits of user data. This is important on systems where an int type contains more than 4 bytes. For example that all amd64 systems. \endenglish \russian Пользовательские данные. Могут быть установлены пользователем для его удобства. Каждый элемент массива хранит только 32 бита пользовательских данных. Это важно на системах где тип int содержит больше чем 4 байта. Например это все системы amd64.\endrussian */
	} nonvolatile_memory_t;

/**  
	* \english
	* EMF settings.
	* This structure contains the data for Electromechanical characteristics(EMF) of the motor.
	* They determine the inductance, resistance and Electromechanical coefficient of the motor.
	* This data is stored in the flash memory of the controller.
	* Please download the new settings when you change the motor.
	* Remember that improper settings of the EMF may damage the equipment.
	* \endenglish
	* \russian
	* Настройки EMF.
	* Эта структура содержит данные электромеханических характеристик(EMF) двигателя.
	* Они определяют индуктивность, сопротивление и электромеханический коэффициент двигателя.
	* Эти данные хранятся во flash памяти памяти контроллера.
	* Пожалуйста, загружайте новые настройки, когда вы меняете мотор.
	* Помните, что неправильные настройки EMF могут повредить оборудование.
	* \endrussian
	* @see set_emf_settings
	* @see get_emf_settings
	* @see get_emf_settings, set_emf_settings
	*/
	typedef struct
	{
		float L;	/**< \english The inductance of the windings of the motor. \endenglish \russian Индуктивность обмоток двигателя. \endrussian */
		float R;	/**< \english The resistance of the windings of the motor. \endenglish \russian Сопротивление обмоток двигателя. \endrussian */
		float Km;	/**< \english Electromechanical ratio of the motor. \endenglish \russian Электромеханический коэффициент двигателя. \endrussian */
		unsigned int BackEMFFlags;	/**< \english \ref flagset_backemfflags "Flags of auto-detection of characteristics of windings of the engine". \endenglish \russian \ref flagset_backemfflags "Флаги автоопределения характеристик обмоток двигателя". \endrussian */
	} emf_settings_t;

/**  
	* \english
	* EAS settings.
	* This structure is intended for setting parameters of algorithms that cannot be attributed to standard Kp, Ki, Kd, and L, R, Km.
	* \endenglish
	* \russian
	* Настройки EAS.
	* Эта структура предназначена для настройки параметров алгоритмов, которые невозможно отнести к стандартным Kp, Ki, Kd и L, R, Km.
	* Эти данные хранятся во flash памяти памяти контроллера.
	* \endrussian
	* @see set_engine_advansed_setup
	* @see get_engine_advansed_setup
	* @see get_engine_advansed_setup, set_engine_advansed_setup
	*/
	typedef struct
	{
		unsigned int stepcloseloop_Kw;	/**< \english Mixing ratio of the actual and set speed, range [0, 100], default value 50. \endenglish \russian Коэффициент смешения реальной и заданной скорости, диапазон [0, 100], значение по умолчанию 50. \endrussian */
		unsigned int stepcloseloop_Kp_low;	/**< \english Position feedback in the low-speed zone, range [0, 65535], default value 1000. \endenglish \russian Обратная связь по позиции в зоне малых скоростей, диапазон [0, 65535], значение по умолчанию 1000. \endrussian */
		unsigned int stepcloseloop_Kp_high;	/**< \english Position feedback in the high-speed zone, range [0, 65535], default value 33. \endenglish \russian Обратная связь по позиции в зоне больших скоростей, диапазон [0, 65535], значение по умолчанию 33. \endrussian */
	} engine_advansed_setup_t;

/**  
	* \english
	* EST settings.
	* This structure EST.
	* \endenglish
	* \russian
	* Настройки EAS.
	* Эта структура EST.
	* Эти данные хранятся во flash памяти контроллера.
	* \endrussian
	* @see set_extended_settings
	* @see get_extended_settings
	* @see get_extended_settings, set_extended_settings
	*/
	typedef struct
	{
		unsigned int Param1;	/**< \english    \endenglish \russian   \endrussian */
	} extended_settings_t;

/** 
	* \english
	* Position information.
	* Useful structure that contains position value in steps and micro for stepper motor
	* and encoder steps of all engines.
	* \endenglish
	* \russian
	* Данные о позиции.
	* Структура содержит значение положения в шагах и
	* микрошагах для шагового двигателя и в шагах энкодера всех
	* двигателей.
	* \endrussian
	* @see get_position
	*/
	typedef struct
	{
		int Position;	/**< \english The position of the whole steps in the engine \endenglish \russian Позиция в основных шагах двигателя \endrussian */
		int uPosition;	/**< \english Microstep position is only used with stepper motors. Microstep size and the range of valid values for this field depend on selected step division mode (see MicrostepMode field in engine_settings). \endenglish \russian Позиция в микрошагах (используется только с шаговыми двигателями). Величина микрошага и диапазон допустимых значений для данного поля зависят от выбранного режима деления шага (см. поле MicrostepMode в engine_settings). \endrussian */
		long_t EncPosition;	/**< \english Encoder position.  \endenglish \russian Позиция энкодера. \endrussian */
	} get_position_t;

/** 
	* \english
	* Position information.
	* Useful structure that contains position value in user units for stepper motor
	* and encoder steps of all engines.
	* \endenglish
	* \russian
	* Данные о позиции.
	* Структура содержит значение положения в пользовательских единицах для шагового двигателя и в шагах энкодера всех
	* двигателей.
	* \endrussian
	* @see get_position
	*/
	typedef struct
	{
		float Position;	/**< \english The position in the engine. Corrected by the table. \endenglish \russian Позиция двигателя. Корректируется таблицей. \endrussian */
		long_t EncPosition;	/**< \english Encoder position.  \endenglish \russian Позиция энкодера. \endrussian */
	} get_position_calb_t;

/** 
	* \english
	* Position information.
	* Useful structure that contains position value in steps and micro for stepper motor
	* and encoder steps of all engines.
	* \endenglish
	* \russian
	* Данные о позиции.
	* Структура содержит значение положения в шагах и
	* микрошагах для шагового двигателя и в шагах энкодера всех
	* двигателей.
	* \endrussian
	* @see set_position
	*/
	typedef struct
	{
		int Position;	/**< \english The position of the whole steps in the engine \endenglish \russian Позиция в основных шагах двигателя \endrussian */
		int uPosition;	/**< \english Microstep position is only used with stepper motors. Microstep size and the range of valid values for this field depend on selected step division mode (see MicrostepMode field in engine_settings). \endenglish \russian Позиция в микрошагах (используется только с шаговыми двигателями). Величина микрошага и диапазон допустимых значений для данного поля зависят от выбранного режима деления шага (см. поле MicrostepMode в engine_settings). \endrussian */
		long_t EncPosition;	/**< \english Encoder position.  \endenglish \russian Позиция энкодера. \endrussian */
		unsigned int PosFlags;	/**< \english \ref flagset_positionflags "Position setting flags". \endenglish \russian \ref flagset_positionflags "Флаги установки положения". \endrussian */
	} set_position_t;

/** 
	* \english
	* Position information which use user units.
	* Useful structure that contains position value in steps and micro for stepper motor
	* and encoder steps of all engines.
	* \endenglish
	* \russian
	* Данные о позиции с использованием пользовательских единиц.
	* Структура содержит значение положения в шагах и
	* микрошагах для шагового двигателя и в шагах энкодера всех
	* двигателей.
	* \endrussian
	* @see set_position
	*/
	typedef struct
	{
		float Position;	/**< \english The position in the engine. \endenglish \russian Позиция двигателя. \endrussian */
		long_t EncPosition;	/**< \english Encoder position.  \endenglish \russian Позиция энкодера. \endrussian */
		unsigned int PosFlags;	/**< \english \ref flagset_positionflags "Position setting flags". \endenglish \russian \ref flagset_positionflags "Флаги установки положения". \endrussian */
	} set_position_calb_t;

/** 
	* \english
	* Device state.
	* Useful structure that contains current controller state, including speed, position and boolean flags.
	* \endenglish
	* \russian
	* Состояние устройства.
	* Эта структура содержит основные параметры текущего состоянии контроллера такие как скорость, позиция и флаги состояния.
	* \endrussian
	* @see get_status_impl
	*/
	typedef struct
	{
		unsigned int MoveSts;	/**< \english \ref flagset_movestate "Flags of move state". \endenglish \russian \ref flagset_movestate "Флаги состояния движения". \endrussian */
		unsigned int MvCmdSts;	/**< \english \ref flagset_mvcmdstatus "Move command state". \endenglish \russian \ref flagset_mvcmdstatus "Состояние команды движения". \endrussian */
		unsigned int PWRSts;	/**< \english \ref flagset_powerstate "Flags of power state of stepper motor". \endenglish \russian \ref flagset_powerstate "Флаги состояния питания шагового мотора". \endrussian */
		unsigned int EncSts;	/**< \english \ref flagset_encodestatus "Encoder state". \endenglish \russian \ref flagset_encodestatus "Состояние энкодера". \endrussian */
		unsigned int WindSts;	/**< \english \ref flagset_windstatus "Winding state". \endenglish \russian \ref flagset_windstatus "Состояние обмоток". \endrussian */
		int CurPosition;	/**< \english Current position. \endenglish \russian Первичное поле, в котором хранится текущая позиция, как бы ни была устроена обратная связь. В случае работы с DC-мотором в этом поле находится текущая позиция по данным с энкодера, в случае работы с ШД-мотором в режиме, когда первичными являются импульсы, подаваемые на мотор, в этом поле содержится целое значение шагов текущей позиции. \endrussian */
		int uCurPosition;	/**< \english Step motor shaft position in microsteps. Microstep size and the range of valid values for this field depend on selected step division mode (see MicrostepMode field in engine_settings). Used only with stepper motor. \endenglish \russian Дробная часть текущей позиции в микрошагах. Величина микрошага и диапазон допустимых значений для данного поля зависят от выбранного режима деления шага (см. поле MicrostepMode в engine_settings). Используется только с шаговым двигателем. \endrussian */
		long_t EncPosition;	/**< \english Current encoder position. \endenglish \russian Текущая позиция по данным с энкодера в импульсах энкодера, используется только если энкодер установлен, активизирован и не является основным датчиком положения, например при использовании энкодера совместно с шаговым двигателем для контроля проскальзования. \endrussian */
		int CurSpeed;	/**< \english Motor shaft speed in steps/s or rpm. \endenglish \russian Текущая скорость. \endrussian */
		int uCurSpeed;	/**< \english Part of motor shaft speed in microsteps. Microstep size and the range of valid values for this field depend on selected step division mode (see MicrostepMode field in engine_settings). Used only with stepper motor. \endenglish \russian Дробная часть текущей скорости в микрошагах. Величина микрошага и диапазон допустимых значений для данного поля зависят от выбранного режима деления шага (см. поле MicrostepMode в engine_settings). Используется только с шаговым двигателем. \endrussian */
		int Ipwr;	/**< \english Engine current, mA. \endenglish \russian Ток потребления силовой части, мА. \endrussian */
		int Upwr;	/**< \english Power supply voltage, tens of mV. \endenglish \russian Напряжение на силовой части, десятки мВ. \endrussian */
		int Iusb;	/**< \english USB current, mA. \endenglish \russian Ток потребления по USB, мА. \endrussian */
		int Uusb;	/**< \english USB voltage, tens of mV. \endenglish \russian Напряжение на USB, десятки мВ. \endrussian */
		int CurT;	/**< \english Temperature in tenths of degrees C. \endenglish \russian Температура процессора в десятых долях градусов цельсия. \endrussian */
		unsigned int Flags;	/**< \english \ref flagset_stateflags "Status flags". \endenglish \russian \ref flagset_stateflags "Флаги состояния". \endrussian */
		unsigned int GPIOFlags;	/**< \english \ref flagset_gpioflags "Status flags of the GPIO outputs". \endenglish \russian \ref flagset_gpioflags "Флаги состояния GPIO входов". \endrussian */
		unsigned int CmdBufFreeSpace;	/**< \english This field is a service field. It shows the amount of free cells buffer synchronization chain. \endenglish \russian Данное поле служебное. Оно показывает количество свободных ячеек буфера цепочки синхронизации. \endrussian */
	} status_t;

/** 
	* \english
	* Device state which use user units.
	* Useful structure that contains current controller state, including speed, position and boolean flags.
	* \endenglish
	* \russian
	* Состояние устройства с использованием пользовательских единиц.
	* Эта структура содержит основные параметры текущего состоянии контроллера такие как скорость, позиция и флаги состояния.
	* \endrussian
	* @see get_status_impl
	*/
	typedef struct
	{
		unsigned int MoveSts;	/**< \english \ref flagset_movestate "Flags of move state". \endenglish \russian \ref flagset_movestate "Флаги состояния движения". \endrussian */
		unsigned int MvCmdSts;	/**< \english \ref flagset_mvcmdstatus "Move command state". \endenglish \russian \ref flagset_mvcmdstatus "Состояние команды движения". \endrussian */
		unsigned int PWRSts;	/**< \english \ref flagset_powerstate "Flags of power state of stepper motor". \endenglish \russian \ref flagset_powerstate "Флаги состояния питания шагового мотора". \endrussian */
		unsigned int EncSts;	/**< \english \ref flagset_encodestatus "Encoder state". \endenglish \russian \ref flagset_encodestatus "Состояние энкодера". \endrussian */
		unsigned int WindSts;	/**< \english \ref flagset_windstatus "Winding state". \endenglish \russian \ref flagset_windstatus "Состояние обмоток". \endrussian */
		float CurPosition;	/**< \english Current position. Corrected by the table. \endenglish \russian Первичное поле, в котором хранится текущая позиция, как бы ни была устроена обратная связь. В случае работы с DC-мотором в этом поле находится текущая позиция по данным с энкодера, в случае работы с ШД-мотором в режиме, когда первичными являются импульсы, подаваемые на мотор. Корректируется таблицей. \endrussian */
		long_t EncPosition;	/**< \english Current encoder position. \endenglish \russian Текущая позиция по данным с энкодера в импульсах энкодера, используется только если энкодер установлен, активизирован и не является основным датчиком положения, например при использовании энкодера совместно с шаговым двигателем для контроля проскальзования. \endrussian */
		float CurSpeed;	/**< \english Motor shaft speed. \endenglish \russian Текущая скорость. \endrussian */
		int Ipwr;	/**< \english Engine current, mA. \endenglish \russian Ток потребления силовой части, мА. \endrussian */
		int Upwr;	/**< \english Power supply voltage, tens of mV. \endenglish \russian Напряжение на силовой части, десятки мВ. \endrussian */
		int Iusb;	/**< \english USB current, mA. \endenglish \russian Ток потребления по USB, мА. \endrussian */
		int Uusb;	/**< \english USB voltage, tens of mV. \endenglish \russian Напряжение на USB, десятки мВ. \endrussian */
		int CurT;	/**< \english Temperature in tenths of degrees C. \endenglish \russian Температура процессора в десятых долях градусов цельсия. \endrussian */
		unsigned int Flags;	/**< \english \ref flagset_stateflags "Status flags". \endenglish \russian \ref flagset_stateflags "Флаги состояния". \endrussian */
		unsigned int GPIOFlags;	/**< \english \ref flagset_gpioflags "Status flags of the GPIO outputs". \endenglish \russian \ref flagset_gpioflags "Флаги состояния GPIO входов". \endrussian */
		unsigned int CmdBufFreeSpace;	/**< \english This field is a service field. It shows the amount of free cells buffer synchronization chain. \endenglish \russian Данное поле служебное. Оно показывает количество свободных ячеек буфера цепочки синхронизации. \endrussian */
	} status_calb_t;

/** 
  * \english
  * The buffer holds no more than 25 points. The exact length of the received buffer is reflected in the Length field.
  * \endenglish
  * \russian
  * Буфер вмещает не более 25и точек. Точная длина полученного буффера отражена в поле Length.
  * \endrussian
  * @see measurements
	* @see get_measurements
  */
	typedef struct
	{
		int Speed[25];	/**< \english Current speed in microsteps per second (whole steps are recalculated taking into account the current step division mode) or encoder counts per second. \endenglish \russian Текущая скорость в микрошагах в секунду (целые шаги пересчитываются с учетом текущего режима деления шага) или отсчетах энкодера в секунду. \endrussian */
		int Error[25];	/**< \english Current error in microsteps per second (whole steps are recalculated taking into account the current step division mode) or encoder counts per second. \endenglish \russian Текущая скорость в микрошагах в секунду (целые шаги пересчитываются с учетом текущего режима деления шага) или отсчетах энкодера в секунду. \endrussian */
		unsigned int Length;	/**< \english Length of actual data in buffer. \endenglish \russian Длина фактических данных в буфере. \endrussian */
	} measurements_t;

/** 
	* \english
	* Additional device state.
	* This structure contains additional values such as winding's voltages, currents and temperature.
	* \endenglish
	* \russian
	* Дополнительное состояние устройства.
	* Эта структура содержит основные дополнительные параметры текущего состоянии контроллера, такие напряжения и токи обмоток и температуру.
	* \endrussian
	* @see get_chart_data
	* @see get_chart_data
	*/
	typedef struct
	{
		int WindingVoltageA;	/**< \english In the case step motor, the voltage across the winding A (in tens of mV); in the case of a brushless, the voltage on the first coil, in the case of the only DC. \endenglish \russian В случае ШД, напряжение на обмотке A (в десятках мВ); в случае бесщеточного, напряжение на первой обмотке; в случае DC на единственной. \endrussian */
		int WindingVoltageB;	/**< \english In the case step motor, the voltage across the winding B (in tens of mV); in case of a brushless, the voltage on the second winding, and in the case of DC is not used. \endenglish \russian В случае ШД, напряжение на обмотке B (в десятках мВ); в случае бесщеточного, напряжение на второй обмотке; в случае DC не используется. \endrussian */
		int WindingVoltageC;	/**< \english In the case of a brushless, the voltage on the third winding (in tens of mV), in the case step motor and DC is not used. \endenglish \russian В случае бесщеточного, напряжение на третьей обмотке (в десятках мВ); в случае ШД и DC не используется. \endrussian */
		int WindingCurrentA;	/**< \english In the case step motor, the current in the coil A (in mA); brushless if the current in the first coil, and in the case of a single DC. \endenglish \russian В случае ШД, ток в обмотке A (в мA); в случае бесщеточного, ток в первой обмотке; в случае DC в единственной. \endrussian */
		int WindingCurrentB;	/**< \english In the case step motor, the current in the coil B (in mA); brushless if the current in the second coil, and in the case of DC is not used. \endenglish \russian В случае ШД, ток в обмотке B (в мА); в случае бесщеточного, ток в второй обмотке; в случае DC не используется. \endrussian */
		int WindingCurrentC;	/**< \english In the case of a brushless, the current in the third winding (in mA), in the case step motor and DC is not used. \endenglish \russian В случае бесщеточного, ток в третьей обмотке (в мА); в случае ШД и DC не используется. \endrussian */
		unsigned int Pot;	/**< \english Analog input value in ten-thousandths. Range: 0..10000 \endenglish \russian Значение на аналоговом входе. Диапазон: 0..10000 \endrussian */
		unsigned int Joy;	/**< \english The joystick position in the ten-thousandths. Range: 0..10000 \endenglish \russian Положение джойстика в десятитысячных долях. Диапазон: 0..10000 \endrussian */
		int DutyCycle;	/**< \english Duty cycle of PWM. \endenglish \russian Коэффициент заполнения ШИМ. \endrussian */
	} chart_data_t;

/** 
	* \english
	* Read command controller information.
	* The controller responds to this command in any state. Manufacturer field for all XI**
	* devices should contain the string "XIMC" (validation is performed on it)
	* The remaining fields contain information about the device.
	* \endenglish
	* \russian
	* Команда чтения информации о контроллере.
	* Контроллер отвечает на эту команду в любом состоянии. Поле Manufacturer для всех XI**
	* девайсов должно содержать строку "XIMC" (по нему производится валидация).
	* Остальные поля содержат информацию об устройстве.
	* \endrussian
	* @see get_device_information
	* @see get_device_information_impl
	*/
	typedef struct
	{
		char Manufacturer[5];	/**< \english Manufacturer \endenglish \russian Производитель \endrussian */
		char ManufacturerId[3];	/**< \english Manufacturer id \endenglish \russian Идентификатор производителя \endrussian */
		char ProductDescription[9];	/**< \english Product description \endenglish \russian Описание продукта \endrussian */
		unsigned int Major;	/**< \english The major number of the hardware version. \endenglish \russian Основной номер версии железа. \endrussian */
		unsigned int Minor;	/**< \english Minor number of the hardware version. \endenglish \russian Второстепенный номер версии железа. \endrussian */
		unsigned int Release;	/**< \english Number of edits this release of hardware. \endenglish \russian Номер правок этой версии железа. \endrussian */
	} device_information_t;

/**  
	* \english
	* Serial number structure and hardware version.
	* The structure keep new serial number, hardware version and valid key.
	* The SN and hardware version are changed and saved when transmitted key matches stored key.
	* Can be used by manufacturer only.
	* \endenglish
	* \russian
	* Структура с серийным номером и версией железа.
	* Вместе с новым серийным номером и версией железа передаётся "Ключ",
	* только при совпадении которого происходит изменение и сохранение.
	* Функция используется только производителем.
	* \endrussian
	* @see set_serial_number
	*/
	typedef struct
	{
		unsigned int SN;	/**< \english New board serial number. \endenglish \russian Новый серийный номер платы. \endrussian */
		uint8_t Key[32];	/**< \english Protection key (256 bit). \endenglish \russian Ключ защиты для установки серийного номера (256 бит). \endrussian */
		unsigned int Major;	/**< \english The major number of the hardware version. \endenglish \russian Основной номер версии железа. \endrussian */
		unsigned int Minor;	/**< \english Minor number of the hardware version. \endenglish \russian Второстепенный номер версии железа. \endrussian */
		unsigned int Release;	/**< \english Number of edits this release of hardware. \endenglish \russian Номер правок этой версии железа. \endrussian */
	} serial_number_t;

/** 
	* \english
	* Analog data.
	* This structure contains raw analog data from ADC embedded on board.
	* These data used for device testing and deep recalibraton by manufacturer only.
	* \endenglish
	* \russian
	* Аналоговые данные.
	* Эта структура содержит необработанные данные с АЦП и нормированные значения.
	* Эти данные используются в сервисных целях для тестирования и калибровки устройства.
	* \endrussian
	* @see get_analog_data
	* @see get_analog_data
	*/
	typedef struct
	{
		unsigned int A1Voltage_ADC;	/**< \english "Voltage on pin 1 winding A" raw data from ADC. \endenglish \russian "Выходное напряжение на 1 выводе обмотки А" необработанные данные с АЦП. \endrussian */
		unsigned int A2Voltage_ADC;	/**< \english "Voltage on pin 2 winding A" raw data from ADC. \endenglish \russian "Выходное напряжение на 2 выводе обмотки А" необработанные данные с АЦП. \endrussian */
		unsigned int B1Voltage_ADC;	/**< \english "Voltage on pin 1 winding B" raw data from ADC. \endenglish \russian "Выходное напряжение на 1 выводе обмотки B" необработанные данные с АЦП. \endrussian */
		unsigned int B2Voltage_ADC;	/**< \english "Voltage on pin 2 winding B" raw data from ADC. \endenglish \russian "Выходное напряжение на 2 выводе обмотки B" необработанные данные с АЦП. \endrussian */
		unsigned int SupVoltage_ADC;	/**< \english "Voltage on the top of MOSFET full bridge" raw data from ADC. \endenglish \russian "Напряжение питания ключей Н-моста" необработанные данные с АЦП. \endrussian */
		unsigned int ACurrent_ADC;	/**< \english "Winding A current" raw data from ADC. \endenglish \russian "Ток через обмотку А" необработанные данные с АЦП. \endrussian */
		unsigned int BCurrent_ADC;	/**< \english "Winding B current" raw data from ADC. \endenglish \russian "Ток через обмотку B" необработанные данные с АЦП. \endrussian */
		unsigned int FullCurrent_ADC;	/**< \english "Full current" raw data from ADC. \endenglish \russian "Полный ток" необработанные данные с АЦП. \endrussian */
		unsigned int Temp_ADC;	/**< \english Voltage from temperature sensor, raw data from ADC. \endenglish \russian Напряжение с датчика температуры, необработанные данные с АЦП. \endrussian */
		unsigned int Joy_ADC;	/**< \english Joystick raw data from ADC. \endenglish \russian Джойстик, необработанные данные с АЦП. \endrussian */
		unsigned int Pot_ADC;	/**< \english Voltage on analog input, raw data from ADC \endenglish \russian Напряжение на аналоговом входе, необработанные данные с АЦП \endrussian */
		unsigned int L5_ADC;	/**< \english USB supply voltage after the current sense resistor, from ADC. \endenglish \russian Напряжение питания USB после current sense резистора, необработанные данные с АЦП. \endrussian */
		unsigned int H5_ADC;	/**< \english Power supply USB from ADC \endenglish \russian Напряжение питания USB, необработанные данные с АЦП \endrussian */
		int A1Voltage;	/**< \english "Voltage on pin 1 winding A" calibrated data (in tens of mV). \endenglish \russian "Выходное напряжение на 1 выводе обмотки А" откалиброванные данные (в десятках мВ). \endrussian */
		int A2Voltage;	/**< \english "Voltage on pin 2 winding A" calibrated data (in tens of mV). \endenglish \russian "Выходное напряжение на 2 выводе обмотки А" откалиброванные данные (в десятках мВ). \endrussian */
		int B1Voltage;	/**< \english "Voltage on pin 1 winding B" calibrated data (in tens of mV). \endenglish \russian "Выходное напряжение на 1 выводе обмотки B" откалиброванные данные (в десятках мВ). \endrussian */
		int B2Voltage;	/**< \english "Voltage on pin 2 winding B" calibrated data (in tens of mV). \endenglish \russian "Выходное напряжение на 2 выводе обмотки B" откалиброванные данные (в десятках мВ). \endrussian */
		int SupVoltage;	/**< \english "Voltage on the top of MOSFET full bridge" calibrated data (in tens of mV). \endenglish \russian "Напряжение питания ключей Н-моста" откалиброванные данные (в десятках мВ). \endrussian */
		int ACurrent;	/**< \english "Winding A current" calibrated data (in mA). \endenglish \russian "Ток через обмотку А" откалиброванные данные (в мА). \endrussian */
		int BCurrent;	/**< \english "Winding B current" calibrated data (in mA). \endenglish \russian "Ток через обмотку B" откалиброванные данные (в мА). \endrussian */
		int FullCurrent;	/**< \english "Full current" calibrated data (in mA). \endenglish \russian "Полный ток" откалиброванные данные (в мА). \endrussian */
		int Temp;	/**< \english Temperature, calibrated data (in tenths of degrees Celcius). \endenglish \russian Температура, откалиброванные данные (в десятых долях градуса Цельсия). \endrussian */
		int Joy;	/**< \english Joystick, calibrated data. Range: 0..10000 \endenglish \russian Джойстик во внутренних единицах. Диапазон: 0..10000 \endrussian */
		int Pot;	/**< \english Analog input, calibrated data. Range: 0..10000 \endenglish \russian Аналоговый вход во внутренних единицах. Диапазон: 0..10000 \endrussian */
		int L5;	/**< \english USB supply voltage after the current sense resistor (in tens of mV). \endenglish \russian Напряжение питания USB после current sense резистора (в десятках мВ). \endrussian */
		int H5;	/**< \english Power supply USB (in tens of mV). \endenglish \russian Напряжение питания USB (в десятках мВ). \endrussian */
		unsigned int deprecated;
		int R;	/**< \english Motor winding resistance in mOhms(is only used with stepper motor). \endenglish \russian Сопротивление обмоток двигателя(для шагового двигателя),  в мОм \endrussian */
		int L;	/**< \english Motor winding pseudo inductance in uHn(is only used with stepper motor). \endenglish \russian Псевдоиндуктивность обмоток двигателя(для шагового двигателя),  в мкГн \endrussian */
	} analog_data_t;

/** 
	* \english
	* Debug data.
	* These data are used for device debugging by manufacturer only.
	* \endenglish
	* \russian
	* Отладочные данные.
	* Эти данные используются в сервисных целях для тестирования и отладки устройства.
	* \endrussian
	* @see get_debug_read
	*/
	typedef struct
	{
		uint8_t DebugData[128];	/**< \english Arbitrary debug data. \endenglish \russian Отладочные данные. \endrussian */
	} debug_read_t;

/** 
	* \english
	* Debug data.
	* These data are used for device debugging by manufacturer only.
	* \endenglish
	* \russian
	* Отладочные данные.
	* Эти данные используются в сервисных целях для тестирования и отладки устройства.
	* \endrussian
	* @see set_debug_write
	*/
	typedef struct
	{
		uint8_t DebugData[128];	/**< \english Arbitrary debug data. \endenglish \russian Отладочные данные. \endrussian */
	} debug_write_t;

/** 
	* \english
	* Stage user name.
	* \endenglish
	* \russian
	* Пользовательское имя подвижки.
	* \endrussian
	* @see get_stage_name, set_stage_name
	*/
	typedef struct
	{
		char PositionerName[17];	/**< \english User positioner name. Can be set by user for his/her convinience. Max string length: 16 chars. \endenglish \russian Пользовательское имя подвижки. Может быть установлено пользователем для его удобства. Максимальная длина строки: 16 символов. \endrussian */
	} stage_name_t;

/** 
	* \english
	* Stage information.
	* \endenglish
	* \russian
	* Информация о позиционере.
	* \endrussian
	* @see set_stage_information
	* @see get_stage_information
	* @see get_stage_information, set_stage_information
	*/
	typedef struct
	{
		char Manufacturer[17];	/**< \english Manufacturer. Max string length: 16 chars. \endenglish \russian Производитель. Максимальная длина строки: 16 символов. \endrussian */
		char PartNumber[25];	/**< \english Series and PartNumber. Max string length: 24 chars. \endenglish \russian Серия и номер модели. Максимальная длина строки: 24 символа. \endrussian */	
	} stage_information_t;

/** 
	* \english
	* Stage settings.
	* \endenglish
	* \russian
	* Настройки позиционера.
	* \endrussian
	* @see set_stage_settings
	* @see get_stage_settings
	* @see get_stage_settings, set_stage_settings
	*/
	typedef struct
	{
		float LeadScrewPitch;	/**< \english Lead screw pitch (mm). Data type: float. \endenglish \russian Шаг ходового винта в мм. Тип данных: float. \endrussian */	
		char Units[9];	/**< \english Units for MaxSpeed and TravelRange fields of the structure (steps, degrees, mm, ...). Max string length: 8 chars. \endenglish \russian Единицы измерения расстояния, используемые в полях MaxSpeed и TravelRange (шаги, градусы, мм, ...), Максимальная длина строки: 8 символов. \endrussian */	
		float MaxSpeed;	/**< \english Max speed (Units/c). Data type: float. \endenglish \russian Максимальная скорость (Units/с). Тип данных: float. \endrussian */	
		float TravelRange;	/**< \english Travel range (Units). Data type: float. \endenglish \russian Диапазон перемещения (Units). Тип данных: float. \endrussian */	
		float SupplyVoltageMin;	/**< \english Supply voltage minimum (V). Data type: float. \endenglish \russian Минимальное напряжение питания (В). Тип данных: float. \endrussian */	
		float SupplyVoltageMax;	/**< \english Supply voltage maximum (V). Data type: float. \endenglish \russian Максимальное напряжение питания (В). Тип данных: float. \endrussian */	
		float MaxCurrentConsumption;	/**< \english Max current consumption (A). Data type: float. \endenglish \russian Максимальный ток потребления (А). Тип данных: float. \endrussian */	
		float HorizontalLoadCapacity;	/**< \english Horizontal load capacity (kg). Data type: float. \endenglish \russian Горизонтальная грузоподъемность (кг). Тип данных: float. \endrussian */	
		float VerticalLoadCapacity;	/**< \english Vertical load capacity (kg). Data type: float. \endenglish \russian Вертикальная грузоподъемность (кг). Тип данных: float. \endrussian */	
	} stage_settings_t;

/** 
	* \english
	* motor information.
	* \endenglish
	* \russian
	* Информация о двигателе.
	* \endrussian
	* @see set_motor_information
	* @see get_motor_information
	* @see get_motor_information, set_motor_information
	*/
	typedef struct
	{
		char Manufacturer[17];	/**< \english Manufacturer. Max string length: 16 chars. \endenglish \russian Производитель. Максимальная длина строки: 16 символов. \endrussian */	
		char PartNumber[25];	/**< \english Series and PartNumber. Max string length: 24 chars. \endenglish \russian Серия и номер модели. Максимальная длина строки: 24 символа. \endrussian */	
	} motor_information_t;

/** 
	* \english
	* Physical characteristics and limitations of the motor.
	* \endenglish
	* \russian
	* Физический характеристики и ограничения мотора.
	* \endrussian
	* @see set_motor_settings
	* @see get_motor_settings
	* @see get_motor_settings, set_motor_settings
	*/
	typedef struct
	{
		unsigned int MotorType;	/**< \english \ref flagset_motortypeflags "Motor Type flags". \endenglish \russian \ref flagset_motortypeflags "Флаги типа двигателя". \endrussian */
		unsigned int ReservedField;	/**< \english Reserved \endenglish \russian Зарезервировано \endrussian */
		unsigned int Poles;	/**< \english Number of pole pairs for DC or BLDC motors or number of steps per rotation for stepper motor. \endenglish \russian Кол-во пар полюсов у DС или BLDC двигателя или кол-во шагов на оборот для шагового двигателя. \endrussian */
		unsigned int Phases;	/**< \english Number of phases for BLDC motors. \endenglish \russian Кол-во фаз у BLDC двигателя. \endrussian */
		float NominalVoltage;	/**< \english Nominal voltage on winding (B). Data type: float \endenglish \russian Номинальное напряжение на обмотке (В). Тип данных: float. \endrussian */
		float NominalCurrent;	/**< \english Maximum direct current in winding for DC and BLDC engines, nominal current in windings for stepper motor (A). Data type: float.  \endenglish \russian Максимальный постоянный ток в обмотке для DC и BLDC двигателей, номинальный ток в обмотке для шаговых двигателей (А). Тип данных: float. \endrussian */
		float NominalSpeed;	/**< \english Not used. Nominal speed(rpm). Used for DC and BLDC engine. Data type: float. \endenglish \russian Не используется. Номинальная скорость (об/мин). Применяется для DC и BLDC двигателей. Тип данных: float. \endrussian */
		float NominalTorque;	/**< \english Nominal torque(mN m). Used for DC and BLDC engine. Data type: float. \endenglish \russian Номинальный крутящий момент (мН м). Применяется для DC и BLDC двигателей. Тип данных: float. \endrussian */
		float NominalPower;	/**< \english Nominal power(W). Used for DC and BLDC engine. Data type: float. \endenglish \russian Номинальная мощность(Вт). Применяется для DC и BLDC двигателей. Тип данных: float. \endrussian */	
		float WindingResistance;	/**< \english Resistance of windings for DC engine, each of two windings for stepper motor or each of there windings for BLDC engine(Ohm). Data type: float.\endenglish \russian Сопротивление обмотки DC двигателя, каждой из двух обмоток шагового двигателя или каждой из трёх обмоток BLDC двигателя (Ом). Тип данных: float. \endrussian */
		float WindingInductance;	/**< \english Inductance of windings for DC engine, each of two windings for stepper motor or each of there windings for BLDC engine(mH). Data type: float.\endenglish \russian Индуктивность обмотки DC двигателя, каждой из двух обмоток шагового двигателя или каждой из трёх обмоток BLDC двигателя (мГн). Тип данных: float. \endrussian */
		float RotorInertia;	/**< \english Rotor inertia(g cm2). Data type: float.\endenglish \russian Инерция ротора (г cм2). Тип данных: float. \endrussian */
		float StallTorque;	/**< \english Torque hold position for a stepper motor or torque at a motionless rotor for other types of engines (mN m). Data type: float. \endenglish \russian Крутящий момент удержания позиции для шагового двигателя или крутящий момент при неподвижном роторе для других типов двигателей (мН м). Тип данных: float. \endrussian */
		float DetentTorque;	/**< \english Holding torque position with un-powered coils (mN m). Data type: float. \endenglish \russian Момент удержания позиции с незапитанными обмотками (мН м). Тип данных: float. \endrussian */
		float TorqueConstant;	/**< \english Torque constant, which determines the aspect ratio of maximum moment of force from the rotor current flowing in the coil (mN m / A). Used mainly for DC motors. Data type: float. \endenglish \russian Константа крутящего момента, определяющая коэффициент пропорциональности максимального момента силы ротора от протекающего в обмотке тока (мН м/А). Используется в основном для DC двигателей. Тип данных: float. \endrussian */
		float SpeedConstant;	/**< \english Velocity constant, which determines the value or amplitude of the induced voltage on the motion of DC or BLDC motor (rpm / V) or stepper motor (steps/s / V). Data type: float. \endenglish \russian Константа скорости, определяющая значение или амплитуду напряжения наведённой индукции при вращении ротора DC или BLDC двигателя (об/мин / В) или шагового двигателя (шаг/с / В). Тип данных: float. \endrussian */
		float SpeedTorqueGradient;	/**< \english Speed torque gradient (rpm / mN m). Data type: float. \endenglish \russian Градиент крутящего момента (об/мин / мН м). Тип данных: float. \endrussian */
		float MechanicalTimeConstant;	/**< \english Mechanical time constant (ms). Data type: float. \endenglish \russian Механическая постоянная времени (мс). Тип данных: float. \endrussian */
		float MaxSpeed;	/**< \english The maximum speed for stepper motors (steps/s) or DC and BLDC motors (rmp). Data type: float. \endenglish \russian Максимальная разрешённая скорость для шаговых двигателей (шаг/с) или для DC и BLDC двигателей (об/мин). Тип данных: float. \endrussian */
		float MaxCurrent;	/**< \english The maximum current in the winding (A). Data type: float. \endenglish \russian Максимальный ток в обмотке (А). Тип данных: float. \endrussian */
		float MaxCurrentTime;	/**< \english Safe duration of overcurrent in the winding (ms). Data type: float. \endenglish \russian Безопасная длительность максимального тока в обмотке (мс). Тип данных: float. \endrussian */
		float NoLoadCurrent;	/**< \english The current consumption in idle mode (A). Used for DC and BLDC motors. Data type: float. \endenglish \russian Ток потребления в холостом режиме (А). Применяется для DC и BLDC двигателей. Тип данных: float. \endrussian */
		float NoLoadSpeed;	/**< \english Idle speed (rpm). Used for DC and BLDC motors. Data type: float. \endenglish \russian Скорость в холостом режиме (об/мин). Применяется для DC и BLDC двигателей. Тип данных: float. \endrussian */
	} motor_settings_t;

/** 
	* \english
	* Encoder information.
	* \endenglish
	* \russian
	* Информация об энкодере.
	* \endrussian
	* @see set_encoder_information
	* @see get_encoder_information
	* @see get_encoder_information, set_encoder_information
	*/
	typedef struct
	{
		char Manufacturer[17];	/**< \english Manufacturer. Max string length: 16 chars. \endenglish \russian Производитель. Максимальная длина строки: 16 символов. \endrussian */	
		char PartNumber[25];	/**< \english Series and PartNumber. Max string length: 24 chars. \endenglish \russian Серия и номер модели. Максимальная длина строки: 24 символа. \endrussian */	
	} encoder_information_t;

/** 
	* \english
	* Encoder settings.
	* \endenglish
	* \russian
	* Настройки энкодера.
	* \endrussian
	* @see set_encoder_settings
	* @see get_encoder_settings
	* @see get_encoder_settings, set_encoder_settings
	*/
	typedef struct
	{
		float MaxOperatingFrequency;	/**< \english Max operation frequency (kHz). Data type: float. \endenglish \russian Максимальная частота (кГц). Тип данных: float. \endrussian */
		float SupplyVoltageMin;	/**< \english Minimum supply voltage (V). Data type: float. \endenglish \russian Минимальное напряжение питания (В). Тип данных: float. \endrussian */
		float SupplyVoltageMax;	/**< \english Maximum supply voltage (V). Data type: float. \endenglish \russian Максимальное напряжение питания (В). Тип данных: float. \endrussian */
		float MaxCurrentConsumption;	/**< \english Max current consumption (mA). Data type: float. \endenglish \russian Максимальное потребление тока (мА). Тип данных: float. \endrussian */
		unsigned int PPR;	/**< \english The number of counts per revolution \endenglish \russian Количество отсчётов на оборот \endrussian */
		unsigned int EncoderSettings;	/**< \english \ref flagset_encodersettingsflags "Encoder settings flags". \endenglish \russian \ref flagset_encodersettingsflags "Флаги настроек энкодера". \endrussian */
	} encoder_settings_t;

/** 
	* \english
	* Hall sensor information.
	* \endenglish
	* \russian
	* Информация о датчиках Холла.
	* \endrussian
	* @see set_hallsensor_information
	* @see get_hallsensor_information
	* @see get_hallsensor_information, set_hallsensor_information
	*/
	typedef struct
	{
		char Manufacturer[17];	/**< \english Manufacturer. Max string length: 16 chars. \endenglish \russian Производитель. Максимальная длина строки: 16 символов. \endrussian */	
		char PartNumber[25];	/**< \english Series and PartNumber. Max string length: 24 chars. \endenglish \russian Серия и номер модели. Максимальная длина строки: 24 символа. \endrussian */	
	} hallsensor_information_t;

/** 
	* \english
	* Hall sensor settings.
	* \endenglish
	* \russian
	* Настройки датчиков Холла.
	* \endrussian
	* @see set_hallsensor_settings
	* @see get_hallsensor_settings
	* @see get_hallsensor_settings, set_hallsensor_settings
	*/
	typedef struct
	{
		float MaxOperatingFrequency;	/**< \english Max operation frequency (kHz). Data type: float. \endenglish \russian Максимальная частота (кГц). Тип данных: float. \endrussian */
		float SupplyVoltageMin;	/**< \english Minimum supply voltage (V). Data type: float. \endenglish \russian Минимальное напряжение питания (В). Тип данных: float. \endrussian */
		float SupplyVoltageMax;	/**< \english Maximum supply voltage (V). Data type: float. \endenglish \russian Максимальное напряжение питания (В). Тип данных: float. \endrussian */
		float MaxCurrentConsumption;	/**< \english Max current consumption (mA). Data type: float. \endenglish \russian Максимальное потребление тока (мА). Тип данных: float. \endrussian */
		unsigned int PPR;	/**< \english The number of counts per revolution \endenglish \russian Количество отсчётов на оборот \endrussian */
	} hallsensor_settings_t;

/** 
	* \english
	* Gear information.
	* \endenglish
	* \russian
	* Информация о редукторе.
	* \endrussian
	* @see set_gear_information
	* @see get_gear_information
	* @see get_gear_information, set_gear_information
	*/
	typedef struct
	{
		char Manufacturer[17];	/**< \english Manufacturer. Max string length: 16 chars. \endenglish \russian Производитель. Максимальная длина строки: 16 символов. \endrussian */	
		char PartNumber[25];	/**< \english Series and PartNumber. Max string length: 24 chars. \endenglish \russian Серия и номер модели. Максимальная длина строки: 24 символа. \endrussian */	
	} gear_information_t;

/** 
	* \english
	* Gear setings.
	* \endenglish
	* \russian
	* Настройки редуктора.
	* \endrussian
	* @see set_gear_settings
	* @see get_gear_settings
	* @see get_gear_settings, set_gear_settings
	*/
	typedef struct
	{
		float ReductionIn;	/**< \english Input reduction coefficient. (Output = (ReductionOut / ReductionIn) * Input) Data type: float. \endenglish \russian Входной коэффициент редуктора. (Выход = (ReductionOut/ReductionIn) * вход) Тип данных: float. \endrussian */
		float ReductionOut;	/**< \english Output reduction coefficient. (Output = (ReductionOut / ReductionIn) * Input) Data type: float. \endenglish \russian Выходной коэффициент редуктора. (Выход = (ReductionOut/ReductionIn) * вход) Тип данных: float. \endrussian */
		float RatedInputTorque;	/**< \english Max continuous torque (N m). Data type: float. \endenglish \russian Максимальный крутящий момент (Н м). Тип данных: float. \endrussian */
		float RatedInputSpeed;	/**< \english Max speed on the input shaft (rpm). Data type: float. \endenglish \russian Максимальная скорость на входном валу редуктора (об/мин). Тип данных: float. \endrussian */
		float MaxOutputBacklash;	/**< \english Output backlash of the reduction gear(degree). Data type: float. \endenglish \russian Выходной люфт редуктора (градус). Тип данных: float.\endrussian */
		float InputInertia;	/**< \english Equivalent input gear inertia (g cm2). Data type: float. \endenglish \russian Эквивалентная входная инерция редуктора(г см2). Тип данных: float. \endrussian */
		float Efficiency;	/**< \english Reduction gear efficiency (%). Data type: float. \endenglish \russian КПД редуктора (%). Тип данных: float. \endrussian */
	} gear_settings_t;

/** 
	* \english
	* Additional accessories information.
	* \endenglish
	* \russian
	* Информация о дополнительных аксессуарах.
	* \endrussian
	* @see set_accessories_settings
	* @see get_accessories_settings
	* @see get_accessories_settings, set_accessories_settings
	*/
	typedef struct
	{
		char MagneticBrakeInfo[25];	/**< \english The manufacturer and the part number of magnetic brake, the maximum string length is 24 characters. \endenglish \russian Производитель и номер магнитного тормоза, Максимальная длина строки: 24 символов. \endrussian */ 
		float MBRatedVoltage;	/**< \english Rated voltage for controlling the magnetic brake (B). Data type: float. \endenglish \russian Номинальное напряжение для управления магнитным тормозом (В). Тип данных: float. \endrussian */
		float MBRatedCurrent;	/**< \english Rated current for controlling the magnetic brake (A). Data type: float. \endenglish \russian Номинальный ток для управления магнитным тормозом (А). Тип данных: float. \endrussian */ 
		float MBTorque;	/**< \english Retention moment (mN m). Data type: float. \endenglish \russian Удерживающий момент (мН м). Тип данных: float. \endrussian */ 
		unsigned int MBSettings;	/**< \english \ref flagset_mbsettingsflags "Magnetic brake settings flags". \endenglish \russian \ref flagset_mbsettingsflags "Флаги настроек энкодера". \endrussian */
		char TemperatureSensorInfo[25];	/**< \english The manufacturer and the part number of the temperature sensor, the maximum string length: 24 characters. \endenglish \russian Производитель и номер температурного датчика, Максимальная длина строки: 24 символов. \endrussian */ 
		float TSMin;	/**< \english The minimum measured temperature (degrees Celsius) Data type: float. \endenglish \russian Минимальная измеряемая температура (град Цельсия). Тип данных: float. \endrussian */ 
		float TSMax;	/**< \english The maximum measured temperature (degrees Celsius) Data type: float. \endenglish \russian Максимальная измеряемая температура (град Цельсия) Тип данных: float. \endrussian */ 
		float TSGrad;	/**< \english The temperature gradient (V/degrees Celsius). Data type: float. \endenglish \russian Температурный градиент (В/град Цельсия). Тип данных: float. \endrussian */ 
		unsigned int TSSettings;	/**< \english \ref flagset_tssettingsflags "Temperature sensor settings flags". \endenglish \russian \ref flagset_tssettingsflags "Флаги настроек температурного датчика". \endrussian */
		unsigned int LimitSwitchesSettings;	/**< \english \ref flagset_lsflags "Temperature sensor settings flags". \endenglish \russian \ref flagset_lsflags "Флаги настроек температурного датчика". \endrussian */
	} accessories_settings_t;

/** 
	* \english
	* Random key.
	* Structure that contains random key used in encryption of WKEY and SSER command contents.
	* \endenglish
	* \russian
	* Случайный ключ.
	* Структура которая содержит случайный ключ, использующийся для шифрования содержимого команд WKEY и SSER.
	* \endrussian
	* @see get_init_random
	*/
	typedef struct
	{
		uint8_t key[16];	/**< \english Random key. \endenglish \russian Случайный ключ. \endrussian */
	} init_random_t;

/** 
  * \english
  * Globally unique identifier.
  * \endenglish
  * \russian
  * Глобальный уникальный идентификатор.
  * \endrussian
	* @see get_globally_unique_identifier
  */
	typedef struct
	{
		unsigned int UniqueID0;	/**< \english Unique ID 0. \endenglish \russian Уникальный ID 0. \endrussian */
		unsigned int UniqueID1;	/**< \english Unique ID 1. \endenglish \russian Уникальный ID 1. \endrussian */
		unsigned int UniqueID2;	/**< \english Unique ID 2. \endenglish \russian Уникальный ID 2. \endrussian */
		unsigned int UniqueID3;	/**< \english Unique ID 3. \endenglish \russian Уникальный ID 3. \endrussian */
	} globally_unique_identifier_t;

/*
 --------------------------------------------
   BEGIN OF GENERATED function declarations
 --------------------------------------------
*/

/**
	* \english
	* @name Controller settings setup
	* Functions for adjusting engine read/write almost all controller settings.
	* \endenglish
	* \russian
	* @name Группа команд настройки контроллера
	* Функции для чтения/записи большинства настроек контроллера.
	* \endrussian
	*/

//@{

/** 
	* \english
	* Feedback settings.
	* @param id an identifier of device
	* @param[in] IPS number of encoder counts per shaft revolution. Range: 1..65535. The field is obsolete, it is recommended to write 0 to IPS and use the extended CountsPerTurn field. You may need to update the controller firmware to the latest version.
	* @param[in] FeedbackType type of feedback
	* @param[in] FeedbackFlags flags of feedback
	* @param[in] CountsPerTurn number of encoder counts per shaft revolution. Range: 1..4294967295. To use the CountsPerTurn field, write 0 in the IPS field, otherwise the value from the IPS field will be used.
	* \endenglish
	* \russian
	* Запись настроек обратной связи.
	* @param id идентификатор устройства
	* @param[in] IPS количество отсчётов энкодера на оборот вала. Диапазон: 1..65535. Поле устарело, рекомендуется записывать 0 в IPS и использовать расширенное поле CountsPerTurn. Может потребоваться обновление микропрограммы контроллера до последней версии.
	* @param[in] FeedbackType тип обратной связи
	* @param[in] FeedbackFlags флаги обратной связи
	* @param[in] CountsPerTurn количество отсчётов энкодера на оборот вала. Диапазон: 1..4294967295. Для использования поля CountsPerTurn нужно записать 0 в поле IPS, иначе будет использоваться значение из поля IPS.
	* \endrussian
	*/
	result_t XIMC_API set_feedback_settings (device_t id, const feedback_settings_t* feedback_settings);

/** 
	* \english
	* Feedback settings.
	* @param id an identifier of device
	* @param[out] IPS number of encoder counts per shaft revolution. Range: 1..65535. The field is obsolete, it is recommended to write 0 to IPS and use the extended CountsPerTurn field. You may need to update the controller firmware to the latest version.
	* @param[out] FeedbackType type of feedback
	* @param[out] FeedbackFlags flags of feedback
	* @param[out] CountsPerTurn number of encoder counts per shaft revolution. Range: 1..4294967295. To use the CountsPerTurn field, write 0 in the IPS field, otherwise the value from the IPS field will be used.
	* \endenglish
	* \russian
	* Чтение настроек обратной связи
	* @param id идентификатор устройства
	* @param[out] IPS количество отсчётов энкодера на оборот вала. Диапазон: 1..65535. Поле устарело, рекомендуется записывать 0 в IPS и использовать расширенное поле CountsPerTurn. Может потребоваться обновление микропрограммы контроллера до последней версии.
	* @param[out] FeedbackType тип обратной связи
	* @param[out] FeedbackFlags флаги обратной связи
	* @param[out] CountsPerTurn количество отсчётов энкодера на оборот вала. Диапазон: 1..4294967295. Для использования поля CountsPerTurn нужно записать 0 в поле IPS, иначе будет использоваться значение из поля IPS.
	* \endrussian
	*/
	result_t XIMC_API get_feedback_settings (device_t id, feedback_settings_t* feedback_settings);

/** 
	* \english
	* Set home settings.
	* This function send structure with calibrating position settings to controller's memory.
	* @see home_settings_t
	* @param id an identifier of device
	* @param[in] home_settings calibrating position settings
	* \endenglish
	* \russian
	* Команда записи настроек для подхода в home position.
	* Эта функция записывает структуру настроек, использующихся для калибровки позиции, в память контроллера.
	* @see home_settings_t
	* @param id идентификатор устройства
	* @param[out] home_settings настройки калибровки позиции
	* \endrussian
	*/
	result_t XIMC_API set_home_settings (device_t id, const home_settings_t* home_settings);

/** 
	* \english
	* Set home settings which use user units.
	* This function send structure with calibrating position settings to controller's memory.
	* @see home_settings_calb_t
	* @param id an identifier of device
	* @param[in] home_settings_calb calibrating position settings
	* @param calibration user unit settings
	* \endenglish
	* \russian
	* Команда записи настроек для подхода в home position с использованием пользовательских единиц.
	* Эта функция записывает структуру настроек, использующихся для калибровки позиции, в память контроллера.
	* @see home_settings_calb_t
	* @param id идентификатор устройства
	* @param[in] home_settings_calb настройки калибровки позиции
	* @param calibration настройки пользовательских единиц
	* \endrussian
	*/
	result_t XIMC_API set_home_settings_calb (device_t id, const home_settings_calb_t* home_settings_calb, const calibration_t* calibration);

/** 
	* \english
	* Read home settings.
	* This function fill structure with settings of calibrating position.
	* @see home_settings_t
	* @param id an identifier of device
	* @param[out] home_settings calibrating position settings
	* \endenglish
	* \russian
	* Команда чтения настроек для подхода в home position.
	* Эта функция заполняет структуру настроек, использующихся для калибровки позиции, в память контроллера.
	* @see home_settings_t
	* @param id идентификатор устройства
	* @param[out] home_settings настройки калибровки позиции
	* \endrussian
	*/
	result_t XIMC_API get_home_settings (device_t id, home_settings_t* home_settings);

/** 
	* \english
	* Read home settings which use user units.
	* This function fill structure with settings of calibrating position.
	* @see home_settings_calb_t
	* @param id an identifier of device
	* @param[out] home_settings_calb calibrating position settings
	* @param calibration user unit settings
	* \endenglish
	* \russian
	* Команда чтения настроек для подхода в home position с использованием пользовательских единиц.
	* Эта функция заполняет структуру настроек, использующихся для калибровки позиции, в память контроллера.
	* @see home_settings_calb_t
	* @param id идентификатор устройства
	* @param[out] home_settings_calb настройки калибровки позиции
	* @param calibration настройки пользовательских единиц
	* \endrussian
	*/
	result_t XIMC_API get_home_settings_calb (device_t id, home_settings_calb_t* home_settings_calb, const calibration_t* calibration);

/** 
	* \english
	* Set command setup movement (speed, acceleration, threshold and etc).
	* @param id an identifier of device
	* @param[in] move_settings structure contains move settings: speed, acceleration, deceleration etc.
	* \endenglish
	* \russian
	* Команда записи настроек перемещения (скорость, ускорение, threshold и скорость в режиме антилюфта).
	* @param id идентификатор устройства
	* @param[in] move_settings структура, содержащая настройки движения: скорость, ускорение, и т.д.
	* \endrussian
	*/
	result_t XIMC_API set_move_settings (device_t id, const move_settings_t* move_settings);

/** 
	* \english
	* Set command setup movement which use user units (speed, acceleration, threshold and etc).
	* @param id an identifier of device
	* @param[in] move_settings_calb structure contains move settings: speed, acceleration, deceleration etc.
	* @param calibration user unit settings
	* \endenglish
	* \russian
	* Команда записи настроек перемещения, с использованием пользовательских единиц (скорость, ускорение, threshold и скорость в режиме антилюфта).
	* @param id идентификатор устройства
	* @param[in] move_settings_calb структура, содержащая настройки движения: скорость, ускорение, и т.д.
	* @param calibration настройки пользовательских единиц
	* \endrussian
	*/
	result_t XIMC_API set_move_settings_calb (device_t id, const move_settings_calb_t* move_settings_calb, const calibration_t* calibration);

/** 
	* \english
	* Read command setup movement (speed, acceleration, threshold and etc).
	* @param id an identifier of device
	* @param[out] move_settings structure contains move settings: speed, acceleration, deceleration etc.
	* \endenglish
	* \russian
	* Команда чтения настроек перемещения (скорость, ускорение, threshold и скорость в режиме антилюфта).
	* @param id идентификатор устройства
	* @param[out] move_settings структура, содержащая настройки движения: скорость, ускорение, и т.д.
	* \endrussian
	*/
	result_t XIMC_API get_move_settings (device_t id, move_settings_t* move_settings);

/** 
	* \english
	* Read command setup movement which use user units (speed, acceleration, threshold and etc).
	* @param id an identifier of device
	* @param[out] move_settings_calb structure contains move settings: speed, acceleration, deceleration etc.
	* @param calibration user unit settings
	* \endenglish
	* \russian
	* Команда чтения настроек перемещения  с использованием пользовательских единиц(скорость, ускорение, threshold и скорость в режиме антилюфта).
	* @param id идентификатор устройства
	* @param[out] move_settings_calb структура, содержащая настройки движения: скорость, ускорение, и т.д.
	* @param calibration настройки пользовательских единиц
	* \endrussian
	*/
	result_t XIMC_API get_move_settings_calb (device_t id, move_settings_calb_t* move_settings_calb, const calibration_t* calibration);

/** 
	* \english
	* Set engine settings.
	* This function send structure with set of engine settings to controller's memory.
	* These settings specify motor shaft movement algorithm, list of limitations and rated characteristics.
	* Use it when you change motor, encoder, positioner etc.
	* Please note that wrong engine settings lead to device malfunction, can lead to irreversible damage of board.
	* @see get_engine_settings
	* @param id an identifier of device
	* @param[in] engine_settings engine settings
	* \endenglish
	* \russian
	* Запись настроек мотора.
	* Настройки определяют номинальные значения напряжения, тока, скорости мотора, характер движения и тип мотора.
	* Пожалуйста, загружайте новые настройки когда вы меняете мотор, энкодер или позиционер.
	* Помните, что неправильные настройки мотора могут повредить оборудование.
	* @see get_engine_settings
	* @param id идентификатор устройства
	* @param[in] engine_settings структура с настройками мотора
	* \endrussian
	*/
	result_t XIMC_API set_engine_settings (device_t id, const engine_settings_t* engine_settings);

/** 
	* \english
	* Set engine settings which use user units.
	* This function send structure with set of engine settings to controller's memory.
	* These settings specify motor shaft movement algorithm, list of limitations and rated characteristics.
	* Use it when you change motor, encoder, positioner etc.
	* Please note that wrong engine settings lead to device malfunction, can lead to irreversible damage of board.
	* @see get_engine_settings
	* @param id an identifier of device
	* @param[in] engine_settings_calb engine settings
	* @param calibration user unit settings
	* \endenglish
	* \russian
	* Запись настроек мотора с использованием пользовательских единиц.
	* Настройки определяют номинальные значения напряжения, тока, скорости мотора, характер движения и тип мотора.
	* Пожалуйста, загружайте новые настройки когда вы меняете мотор, энкодер или позиционер.
	* Помните, что неправильные настройки мотора могут повредить оборудование.
	* @see get_engine_settings
	* @param id идентификатор устройства
	* @param[in] engine_settings_calb структура с настройками мотора
	* @param calibration настройки пользовательских единиц
	* \endrussian
	*/
	result_t XIMC_API set_engine_settings_calb (device_t id, const engine_settings_calb_t* engine_settings_calb, const calibration_t* calibration);

/** 
	* \english
	* Read engine settings.
	* This function fill structure with set of useful motor settings stored in controller's memory.
	* These settings specify motor shaft movement algorithm, list of limitations and rated characteristics.
	* @see set_engine_settings
	* @param id an identifier of device
	* @param[out] engine_settings engine settings
	* \endenglish
	* \russian
	* Чтение настроек мотора.
	* Настройки определяют номинальные значения напряжения, тока, скорости мотора, характер движения и тип мотора.
	* Пожалуйста, загружайте новые настройки когда вы меняете мотор, энкодер или позиционер.
	* Помните, что неправильные настройки мотора могут повредить оборудование.
	* @see set_engine_settings
	* @param id идентификатор устройства
	* @param[out] engine_settings структура с настройками мотора
	* \endrussian
	*/
	result_t XIMC_API get_engine_settings (device_t id, engine_settings_t* engine_settings);

/** 
	* \english
	* Read engine settings which use user units.
	* This function fill structure with set of useful motor settings stored in controller's memory.
	* These settings specify motor shaft movement algorithm, list of limitations and rated characteristics.
	* @see set_engine_settings
	* @param id an identifier of device
	* @param[out] engine_settings_calb engine settings
	* @param calibration user unit settings
	* \endenglish
	* \russian
	* Чтение настроек мотора с использованием пользовательских единиц.
	* Настройки определяют номинальные значения напряжения, тока, скорости мотора, характер движения и тип мотора.
	* Пожалуйста, загружайте новые настройки когда вы меняете мотор, энкодер или позиционер.
	* Помните, что неправильные настройки мотора могут повредить оборудование.
	* @see set_engine_settings
	* @param id идентификатор устройства
	* @param[out] engine_settings_calb структура с настройками мотора
	* @param calibration настройки пользовательских единиц
	* \endrussian
	*/
	result_t XIMC_API get_engine_settings_calb (device_t id, engine_settings_calb_t* engine_settings_calb, const calibration_t* calibration);

/** 
	* \english
	* Set engine type and driver type.
	* @param id an identifier of device
	* @param[in] entype_settings structure contains settings motor type and power driver type
	* \endenglish
	* \russian
	* Запись информации о типе мотора и типе силового драйвера.
	* @param id идентификатор устройства
	* @param[in] entype_settings структура, содержащая настройки типа мотора и типа силового драйвера
	* \endrussian
	*/
	result_t XIMC_API set_entype_settings (device_t id, const entype_settings_t* entype_settings);

/** 
	* \english
	* Return engine type and driver type.
	* @param id an identifier of device
	* @param[out] entype_settings structure contains settings motor type and power driver type
	* \endenglish
	* \russian
	* Возвращает информацию о типе мотора и силового драйвера.
	* @param id идентификатор устройства
	* @param[out] entype_settings структура, содержащая настройки типа мотора и типа силового драйвера
	* \endrussian
	*/
	result_t XIMC_API get_entype_settings (device_t id, entype_settings_t* entype_settings);

/** 
	* \english
	* Set settings of step motor power control.
	* Used with stepper motor only.
	* @param id an identifier of device
	* @param[in] power_settings structure contains settings of step motor power control
	* \endenglish
	* \russian
	* Команда записи параметров питания мотора. Используется только с шаговым двигателем.
	* @param id идентификатор устройства
	* @param[in] power_settings структура, содержащая настройки питания шагового мотора
	* \endrussian
	*/
	result_t XIMC_API set_power_settings (device_t id, const power_settings_t* power_settings);

/** 
	* \english
	* Read settings of step motor power control.
	* Used with stepper motor only.
	* @param id an identifier of device
	* @param[out] power_settings structure contains settings of step motor power control
	* \endenglish
	* \russian
	* Команда чтения параметров питания мотора. Используется только с шаговым двигателем.
	* Используется только с шаговым двигателем.
	* @param id идентификатор устройства
	* @param[out] power_settings структура, содержащая настройки питания шагового мотора
	* \endrussian
	*/
	result_t XIMC_API get_power_settings (device_t id, power_settings_t* power_settings);

/** 
	* \english
	* Set protection settings.
	* @param id an identifier of device
	* @param secure_settings structure with secure data
	* \endenglish
	* \russian
	* Команда записи установок защит.
	* @param id идентификатор устройства
	* @param secure_settings структура с настройками критических значений
	* \endrussian
	* @see status_t::flags
	*/
	result_t XIMC_API set_secure_settings (device_t id, const secure_settings_t* secure_settings);

/** 
	* \english
	* Read protection settings.
	* @param id an identifier of device
	* @param[out] secure_settings critical parameter settings to protect the hardware
	* \endenglish
	* \russian
	* Команда записи установок защит.
	* @param id идентификатор устройства
	* @param[out] secure_settings настройки, определяющие максимально допустимые параметры, для защиты оборудования
	* \endrussian
	* @see status_t::flags
	*/
	result_t XIMC_API get_secure_settings (device_t id, secure_settings_t* secure_settings);

/** 
	* \english
	* Set border and limit switches settings.
	* @see get_edges_settings
	* @param id an identifier of device
	* @param[in] edges_settings edges settings, specify types of borders, motor behaviour and electrical behaviour of limit switches
	* \endenglish
	* \russian
	* Запись настроек границ и концевых выключателей.
	* @see get_edges_settings
	* @param id идентификатор устройства
	* @param[in] edges_settings настройки, определяющие тип границ, поведение мотора при их достижении и параметры концевых выключателей
	* \endrussian
	*/
	result_t XIMC_API set_edges_settings (device_t id, const edges_settings_t* edges_settings);

/** 
	* \english
	* Set border and limit switches settings which use user units.
	* @see get_edges_settings_calb
	* @param id an identifier of device
	* @param[in] edges_settings_calb edges settings, specify types of borders, motor behaviour and electrical behaviour of limit switches
	* @param calibration user unit settings
	* 
	* \note
	* Attention! Some parameters of the edges_settings_calb structure are corrected by the coordinate correction table.
	*
	* \endenglish
	* \russian
	* Запись настроек границ и концевых выключателей с использованием пользовательских единиц.
	* @see get_edges_settings_calb
	* @param id идентификатор устройства
	* @param[in] edges_settings_calb настройки, определяющие тип границ, поведение мотора при их достижении и параметры концевых выключателей
	* @param calibration настройки пользовательских единиц
	*
	* \note
	* Внимание! Некоторые параметры структуры edges_settings_calb корректируются таблицей коррекции координат.  
	*
	* \endrussian
	*/
	result_t XIMC_API set_edges_settings_calb (device_t id, const edges_settings_calb_t* edges_settings_calb, const calibration_t* calibration);

/**  
	* \english
	* Read border and limit switches settings.
	* @see set_edges_settings
	* @param id an identifier of device
	* @param[out] edges_settings edges settings, specify types of borders, motor behaviour and electrical behaviour of limit switches
	* \endenglish
	* \russian
	* Чтение настроек границ и концевых выключателей.
	* @see set_edges_settings
	* @param id идентификатор устройства
	* @param[out] edges_settings настройки, определяющие тип границ, поведение мотора при их достижении и параметры концевых выключателей
	* \endrussian
	*/
	result_t XIMC_API get_edges_settings (device_t id, edges_settings_t* edges_settings);

/**  
	* \english
	* Read border and limit switches settings which use user units.
	* @see set_edges_settings_calb
	* @param id an identifier of device
	* @param[out] edges_settings_calb edges settings, specify types of borders, motor behaviour and electrical behaviour of limit switches
	* @param calibration user unit settings
	* 
	* \note
	* Attention! Some parameters of the edges_settings_calb structure are corrected by the coordinate correction table.
	*
	* \endenglish
	* \russian
	* Чтение настроек границ и концевых выключателей с использованием пользовательских единиц.
	* @see set_edges_settings_calb
	* @param id идентификатор устройства
	* @param[out] edges_settings_calb настройки, определяющие тип границ, поведение мотора при их достижении и параметры концевых выключателей
	* @param calibration настройки пользовательских единиц
	*
	* \note
	* Внимание! Некоторые параметры структуры edges_settings_calb корректируются таблицей коррекции координат.  
	*
	* \endrussian
	*/
	result_t XIMC_API get_edges_settings_calb (device_t id, edges_settings_calb_t* edges_settings_calb, const calibration_t* calibration);

/**  
	* \english
	* Set PID settings.
	* This function send structure with set of PID factors to controller's memory.
	* These settings specify behaviour of PID routine for positioner.
	* These factors are slightly different for different positioners.
	* All boards are supplied with standard set of PID setting on controller's flash memory.
	* Please use it for loading new PID settings when you change positioner.
	* Please note that wrong PID settings lead to device malfunction.
	* @see get_pid_settings
	* @param id an identifier of device
	* @param[in] pid_settings pid settings
	* \endenglish
	* \russian
	* Запись ПИД коэффициентов.
	* Эти коэффициенты определяют поведение позиционера.
	* Коэффициенты различны для разных позиционеров.
	* Пожалуйста, загружайте новые настройки, когда вы меняете мотор или позиционер.
	* @see get_pid_settings
	* @param id идентификатор устройства
	* @param[in] pid_settings настройки ПИД
	* \endrussian
	*/
	result_t XIMC_API set_pid_settings (device_t id, const pid_settings_t* pid_settings);

/**  
	* \english
	* Read PID settings.
	* This function fill structure with set of motor PID settings stored in controller's memory.
	* These settings specify behaviour of PID routine for positioner.
	* These factors are slightly different for different positioners.
	* All boards are supplied with standard set of PID setting on controller's flash memory.
	* @see set_pid_settings
	* @param id an identifier of device
	* @param[out] pid_settings pid settings
	* \endenglish
	* \russian
	* Чтение ПИД коэффициентов.
	* Эти коэффициенты определяют поведение позиционера.
	* Коэффициенты различны для разных позиционеров.
	* @see set_pid_settings
	* @param id идентификатор устройства
	* @param[out] pid_settings настройки ПИД
	* \endrussian
	*/
	result_t XIMC_API get_pid_settings (device_t id, pid_settings_t* pid_settings);

/**  
	* \english
	* Set input synchronization settings.
	* This function send structure with set of input synchronization settings, that specify behaviour of input synchronization, to controller's memory.
	* All boards are supplied with standard set of these settings.
	* @see get_sync_in_settings
	* @param id an identifier of device
	* @param[in] sync_in_settings synchronization settings
	* \endenglish
	* \russian
	* Запись настроек для входного импульса синхронизации.
	* Эта функция записывает структуру с настройками входного импульса синхронизации, определяющими поведение входа синхронизации, в память контроллера.
	* @see get_sync_in_settings
	* @param id идентификатор устройства
	* @param[in] sync_in_settings настройки синхронизации
	* \endrussian
	*/
	result_t XIMC_API set_sync_in_settings (device_t id, const sync_in_settings_t* sync_in_settings);

/**  
	* \english
	* Set input synchronization settings which use user units.
	* This function send structure with set of input synchronization settings, that specify behaviour of input synchronization, to controller's memory.
	* All boards are supplied with standard set of these settings.
	* @see get_sync_in_settings_calb
	* @param id an identifier of device
	* @param[in] sync_in_settings_calb synchronization settings
	* @param calibration user unit settings
	* \endenglish
	* \russian
	* Запись настроек для входного импульса синхронизации с использованием пользовательских единиц.
	* Эта функция записывает структуру с настройками входного импульса синхронизации, определяющими поведение входа синхронизации, в память контроллера.
	* @see get_sync_in_settings_calb
	* @param id идентификатор устройства
	* @param[in] sync_in_settings_calb настройки синхронизации
	* @param calibration настройки пользовательских единиц
	* \endrussian
	*/
	result_t XIMC_API set_sync_in_settings_calb (device_t id, const sync_in_settings_calb_t* sync_in_settings_calb, const calibration_t* calibration);

/**  
	* \english
	* Read input synchronization settings.
	* This function fill structure with set of input synchronization settings, modes, periods and flags, that specify behaviour of input synchronization.
	* All boards are supplied with standard set of these settings.
	* @see set_sync_in_settings
	* @param id an identifier of device
	* @param[out] sync_in_settings synchronization settings
	* \endenglish
	* \russian
	* Чтение настроек для входного импульса синхронизации.
	* Эта функция считывает структуру с настройками синхронизации, определяющими поведение входа синхронизации, в память контроллера.
	* @see set_sync_in_settings
	* @param id идентификатор устройства
	* @param[out] sync_in_settings настройки синхронизации
	* \endrussian
	*/
	result_t XIMC_API get_sync_in_settings (device_t id, sync_in_settings_t* sync_in_settings);

/**  
	* \english
	* Read input synchronization settings which use user units.
	* This function fill structure with set of input synchronization settings, modes, periods and flags, that specify behaviour of input synchronization.
	* All boards are supplied with standard set of these settings.
	* @see set_sync_in_settings_calb
	* @param id an identifier of device
	* @param[out] sync_in_settings_calb synchronization settings
	* @param calibration user unit settings
	* \endenglish
	* \russian
	* Чтение настроек для входного импульса синхронизации с использованием пользовательских единиц.
	* Эта функция считывает структуру с настройками синхронизации, определяющими поведение входа синхронизации, в память контроллера.
	* @see set_sync_in_settings_calb
	* @param id идентификатор устройства
	* @param[out] sync_in_settings_calb настройки синхронизации
	* @param calibration настройки пользовательских единиц
	* \endrussian
	*/
	result_t XIMC_API get_sync_in_settings_calb (device_t id, sync_in_settings_calb_t* sync_in_settings_calb, const calibration_t* calibration);

/** 
	* \english
	* Set output synchronization settings.
	* This function send structure with set of output synchronization settings, that specify behaviour of output synchronization, to controller's memory.
	* All boards are supplied with standard set of these settings.
	* @see get_sync_out_settings
	* @param id an identifier of device
	* @param[in] sync_out_settings synchronization settings
	* \endenglish
	* \russian
	* Запись настроек для выходного импульса синхронизации.
	* Эта функция записывает структуру с настройками выходного импульса синхронизации, определяющими поведение вывода синхронизации, в память контроллера.
	* @see get_sync_in_settings
	* @param id идентификатор устройства
	* @param[in] sync_out_settings настройки синхронизации
	* \endrussian
	*/
	result_t XIMC_API set_sync_out_settings (device_t id, const sync_out_settings_t* sync_out_settings);

/** 
	* \english
	* Set output synchronization settings which use user units.
	* This function send structure with set of output synchronization settings, that specify behaviour of output synchronization, to controller's memory.
	* All boards are supplied with standard set of these settings.
	* @see get_sync_in_settings_calb
	* @param id an identifier of device
	* @param[in] sync_out_settings_calb synchronization settings
	* @param calibration user unit settings
	* \endenglish
	* \russian
	* Запись настроек для выходного импульса синхронизации с использованием пользовательских единиц.
	* Эта функция записывает структуру с настройками выходного импульса синхронизации, определяющими поведение вывода синхронизации, в память контроллера.
	* @see get_sync_in_settings_calb
	* @param id идентификатор устройства
	* @param[in] sync_out_settings_calb настройки синхронизации
	* @param calibration настройки пользовательских единиц
	* \endrussian
	*/
	result_t XIMC_API set_sync_out_settings_calb (device_t id, const sync_out_settings_calb_t* sync_out_settings_calb, const calibration_t* calibration);

/** 
	* \english
	* Read output synchronization settings.
	* This function fill structure with set of output synchronization settings, modes, periods and flags, that specify behaviour of output synchronization.
	* All boards are supplied with standard set of these settings.
	* @see set_sync_out_settings
	* @param id an identifier of device
	* @param[out] sync_out_settings synchronization settings
	* \endenglish
	* \russian
	* Чтение настроек для выходного импульса синхронизации.
	* Эта функция считывает структуру с настройками синхронизации, определяющими поведение выхода синхронизации, в память контроллера.
	* \endrussian
	*/
	result_t XIMC_API get_sync_out_settings (device_t id, sync_out_settings_t* sync_out_settings);

/** 
	* \english
	* Read output synchronization settings which use user units.
	* This function fill structure with set of output synchronization settings, modes, periods and flags, that specify behaviour of output synchronization.
	* All boards are supplied with standard set of these settings.
	* @see set_sync_in_settings_calb
	* @param id an identifier of device
	* @param[out] sync_out_settings_calb synchronization settings
	* @param calibration user unit settings
	* \endenglish
	* \russian
	* Чтение настроек для выходного импульса синхронизации с использованием пользовательских единиц.
	* Эта функция считывает структуру с настройками синхронизации, определяющими поведение выхода синхронизации, в память контроллера.
	* @see set_sync_in_settings_calb
	* @param id идентификатор устройства
	* @param[in] sync_out_settings_calb настройки синхронизации
	* @param calibration настройки пользовательских единиц
	* \endrussian
	*/
	result_t XIMC_API get_sync_out_settings_calb (device_t id, sync_out_settings_calb_t* sync_out_settings_calb, const calibration_t* calibration);

/** 
	* \english
	* Set EXTIO settings.
	* This function writes a structure with a set of EXTIO settings to controller's memory.
	* By default input event are signalled through rising front and output states are signalled by high logic state.
	* @see get_extio_settings
	* @param id an identifier of device
	* @param[in] extio_settings EXTIO settings
	* \endenglish
	* \russian
	* Команда записи параметров настройки режимов внешнего ввода/вывода.
	* Входные события обрабатываются по фронту. Выходные состояния сигнализируются логическим состоянием.
	* По умолчанию нарастающий фронт считается моментом подачи входного сигнала, а единичное состояние считается активным выходом.
	* @see get_extio_settings
	* @param id идентификатор устройства
	* @param[in] extio_settings настройки EXTIO
	* \endrussian
	*/
	result_t XIMC_API set_extio_settings (device_t id, const extio_settings_t* extio_settings);

/** 
	* \english
	* Read EXTIO settings.
	* This function reads a structure with a set of EXTIO settings from controller's memory.
	* @see set_extio_settings
	* @param id an identifier of device
	* @param[out] extio_settings EXTIO settings
	* \endenglish
	* \russian
	* Команда чтения параметров настройки режимов внешнего ввода/вывода.
	* @see set_extio_settings
	* @param id идентификатор устройства
	* @param[out] extio_settings настройки EXTIO
	* \endrussian
	*/
	result_t XIMC_API get_extio_settings (device_t id, extio_settings_t* extio_settings);

/** 
	* \english
	* Set settings of brake control.
	* @param id an identifier of device
	* @param[in] brake_settings structure contains settings of brake control
	* \endenglish
	* \russian
	* Запись настроек управления тормозом.
	* @param id идентификатор устройства
	* @param[in] brake_settings структура, содержащая настройки управления тормозом
	* \endrussian
	*/
	result_t XIMC_API set_brake_settings (device_t id, const brake_settings_t* brake_settings);

/** 
	* \english
	* Read settings of brake control.
	* @param id an identifier of device
	* @param[out] brake_settings structure contains settings of brake control
	* \endenglish
	* \russian
	* Чтение настроек управления тормозом.
	* @param id идентификатор устройства
	* @param[out] brake_settings структура, содержащая настройки управления тормозом
	* \endrussian
	*/
	result_t XIMC_API get_brake_settings (device_t id, brake_settings_t* brake_settings);

/** 
	* \english
	* Set settings of motor control.
	* When choosing CTL_MODE = 1 switches motor control with the joystick.
	* In this mode, the joystick to the maximum engine tends
	* Move at MaxSpeed [i], where i = 0 if the previous use
	* This mode is not selected another i. Buttons switch the room rate i.
	* When CTL_MODE = 2 is switched on motor control using the
	* Left / right. When you click on the button motor starts to move in the appropriate direction at a speed MaxSpeed [0],
	* at the end of time Timeout [i] motor move at a speed MaxSpeed [i+1]. at
	* Transition from MaxSpeed [i] on MaxSpeed [i +1] to acceleration, as usual.
	* @param id an identifier of device
	* @param[in] control_settings structure contains settings motor control by joystick or buttons left/right.
	* \endenglish
	* \russian
	* Запись настроек управления мотором.
	* При выборе CTL_MODE=1 включается управление мотором с помощью джойстика.
	* В этом режиме при отклонении джойстика на максимум двигатель стремится
	* двигаться со скоростью MaxSpeed [i], где i=0, если предыдущим использованием
	* этого режима не было выбрано другое i. Кнопки переключают номер скорости i.
	* При выборе CTL_MODE=2 включается управление мотором с помощью кнопок
	* left/right. При нажатии на кнопки двигатель начинает двигаться в соответствующую сторону со скоростью MaxSpeed [0], по истечении времени Timeout[i] мотор
	* двигается со скоростью MaxSpeed [i+1]. При
	* переходе от MaxSpeed [i] на MaxSpeed [i+1] действует ускорение, как обычно.
	* @param id идентификатор устройства
	* @param[in] control_settings структура, содержащая настройки управления мотором с помощью джойстика или кнопок влево/вправо.
	* \endrussian
	*/
	result_t XIMC_API set_control_settings (device_t id, const control_settings_t* control_settings);

/** 
	* \english
	* Set settings of motor control which use user units.
	* When choosing CTL_MODE = 1 switches motor control with the joystick.
	* In this mode, the joystick to the maximum engine tends
	* Move at MaxSpeed [i], where i = 0 if the previous use
	* This mode is not selected another i. Buttons switch the room rate i.
	* When CTL_MODE = 2 is switched on motor control using the
	* Left / right. When you click on the button motor starts to move in the appropriate direction at a speed MaxSpeed [0],
	* at the end of time Timeout [i] motor move at a speed MaxSpeed [i+1]. at
	* Transition from MaxSpeed [i] on MaxSpeed [i +1] to acceleration, as usual.
	* @param id an identifier of device
	* @param[in] control_settings_calb structure contains settings motor control by joystick or buttons left/right.
	* @param calibration user unit settings
	* \endenglish
	* \russian
	* Запись настроек управления мотором с использованием пользовательских единиц.
	* При выборе CTL_MODE=1 включается управление мотором с помощью джойстика.
	* В этом режиме при отклонении джойстика на максимум двигатель стремится
	* двигаться со скоростью MaxSpeed [i], где i=0, если предыдущим использованием
	* этого режима не было выбрано другое i. Кнопки переключают номер скорости i.
	* При выборе CTL_MODE=2 включается управление мотором с помощью кнопок
	* left/right. При нажатии на кнопки двигатель начинает двигаться в соответствующую сторону со скоростью MaxSpeed [0], по истечении времени Timeout[i] мотор
	* двигается со скоростью MaxSpeed [i+1]. При
	* переходе от MaxSpeed [i] на MaxSpeed [i+1] действует ускорение, как обычно.
	* @param id идентификатор устройства
	* @param[in] control_settings_calb структура, содержащая настройки управления мотором с помощью джойстика или кнопок влево/вправо.
	* @param calibration настройки пользовательских единиц
	* \endrussian
	*/
	result_t XIMC_API set_control_settings_calb (device_t id, const control_settings_calb_t* control_settings_calb, const calibration_t* calibration);

/** 
	* \english
	* Read settings of motor control.
	* When choosing CTL_MODE = 1 switches motor control with the joystick.
	* In this mode, the joystick to the maximum engine tends
	* Move at MaxSpeed [i], where i = 0 if the previous use
	* This mode is not selected another i. Buttons switch the room rate i.
	* When CTL_MODE = 2 is switched on motor control using the
	* Left / right. When you click on the button motor starts to move in the appropriate direction at a speed MaxSpeed [0],
	* at the end of time Timeout [i] motor move at a speed MaxSpeed [i+1]. at
	* Transition from MaxSpeed [i] on MaxSpeed [i +1] to acceleration, as usual.
	* @param id an identifier of device
	* @param[out] control_settings structure contains settings motor control by joystick or buttons left/right.
	* \endenglish
	* \russian
	* Чтение настроек управления мотором.
	* При выборе CTL_MODE=1 включается управление мотором с помощью джойстика.
	* В этом режиме при отклонении джойстика на максимум двигатель стремится
	* двигаться со скоростью MaxSpeed [i], где i=0, если предыдущим использованием
	* этого режима не было выбрано другое i. Кнопки переключают номер скорости i.
	* При выборе CTL_MODE=2 включается управление мотором с помощью кнопок
	* left/right. При нажатии на кнопки двигатель начинает двигаться в соответствующую сторону со скоростью MaxSpeed [0], по истечении времени Timeout[i] мотор
	* двигается со скоростью MaxSpeed [i+1]. При
	* переходе от MaxSpeed [i] на MaxSpeed [i+1] действует ускорение, как обычно.
	* @param id идентификатор устройства
	* @param[out] control_settings структура, содержащая настройки управления мотором с помощью джойстика или кнопок влево/вправо.
	* \endrussian
	*/
	result_t XIMC_API get_control_settings (device_t id, control_settings_t* control_settings);

/** 
	* \english
	* Read settings of motor control which use user units.
	* When choosing CTL_MODE = 1 switches motor control with the joystick.
	* In this mode, the joystick to the maximum engine tends
	* Move at MaxSpeed [i], where i = 0 if the previous use
	* This mode is not selected another i. Buttons switch the room rate i.
	* When CTL_MODE = 2 is switched on motor control using the
	* Left / right. When you click on the button motor starts to move in the appropriate direction at a speed MaxSpeed [0],
	* at the end of time Timeout [i] motor move at a speed MaxSpeed [i+1]. at
	* Transition from MaxSpeed [i] on MaxSpeed [i +1] to acceleration, as usual.
	* @param id an identifier of device
	* @param[out] control_settings_calb structure contains settings motor control by joystick or buttons left/right.
	* @param calibration user unit settings
	* \endenglish
	* \russian
	* Чтение настроек управления мотором с использованием пользовательских единиц.
	* При выборе CTL_MODE=1 включается управление мотором с помощью джойстика.
	* В этом режиме при отклонении джойстика на максимум двигатель стремится
	* двигаться со скоростью MaxSpeed [i], где i=0, если предыдущим использованием
	* этого режима не было выбрано другое i. Кнопки переключают номер скорости i.
	* При выборе CTL_MODE=2 включается управление мотором с помощью кнопок
	* left/right. При нажатии на кнопки двигатель начинает двигаться в соответствующую сторону со скоростью MaxSpeed [0], по истечении времени Timeout[i] мотор
	* двигается со скоростью MaxSpeed [i+1]. При
	* переходе от MaxSpeed [i] на MaxSpeed [i+1] действует ускорение, как обычно.
	* @param id идентификатор устройства
	* @param[out] control_settings_calb структура, содержащая настройки управления мотором с помощью джойстика или кнопок влево/вправо.
	* @param calibration настройки пользовательских единиц
	* \endrussian
	*/
	result_t XIMC_API get_control_settings_calb (device_t id, control_settings_calb_t* control_settings_calb, const calibration_t* calibration);

/** 
	* \english
	* Set settings of joystick.
	* If joystick position is outside DeadZone limits from the central position a movement with speed,
	* defined by the joystick DeadZone edge to 100% deviation, begins. Joystick positions inside DeadZone limits
	* correspond to zero speed (soft stop of motion) and positions beyond Low and High limits correspond MaxSpeed [i]
	* or -MaxSpeed [i] (see command SCTL), where i = 0 by default and can be changed with left/right buttons (see command SCTL).
	* If next speed in list is zero (both integer and microstep parts), the button press is ignored. First speed in list shouldn't be zero.
	* The DeadZone ranges are illustrated on the following picture.
	* !/attachments/download/5563/range25p.png!
	* The relationship between the deviation and the rate is exponential,
	* allowing no switching speed combine high mobility and accuracy. The following picture illustrates this:
	* !/attachments/download/3092/ExpJoystick.png!
	* The nonlinearity parameter is adjustable. Setting it to zero makes deviation/speed relation linear.
	* @param id an identifier of device
	* @param[in] joystick_settings structure contains joystick settings
	* \endenglish
	* \russian
	* Запись настроек джойстика.
	* При отклонении джойстика более чем на DeadZone от центрального положения начинается движение со скоростью,
	* определяемой отклонением джойстика от DeadZone до 100% отклонения, причем отклонению DeadZone соответствует
	* нулевая скорость, а 100% отклонения соответствует MaxSpeed [i] (см. команду SCTL), где i=0, если предыдущим
	* использованием этого режима не было выбрано другое i.
	* Если следующая скорость в таблице скоростей нулевая (целая и микрошаговая части), то перехода на неё не происходит.
	* DeadZone вычисляется в десятых долях процента отклонения
	* от центра (JoyCenter) до правого или левого максимума. Расчёт DeadZone проиллюстрирован на графике: !/attachments/download/5563/range25p.png!
	* Зависимость между отклонением и скоростью экспоненциальная,
	* что позволяет без переключения режимов скорости сочетать высокую подвижность и точность. На графике ниже показан
	* пример экспоненциальной зависимости скорости и работы мертвой зоны.
	* !/attachments/download/3092/ExpJoystick.png!
	* Параметр нелинейнойсти можно менять. Нулевой параметр нелинейности соответствует линейной зависимости.
	* @param id идентификатор устройства
	* @param[in] joystick_settings структура, содержащая настройки джойстика
	* \endrussian
	*/
	result_t XIMC_API set_joystick_settings (device_t id, const joystick_settings_t* joystick_settings);

/** 
	* \english
	* Read settings of joystick.
	* If joystick position is outside DeadZone limits from the central position a movement with speed,
	* defined by the joystick DeadZone edge to 100% deviation, begins. Joystick positions inside DeadZone limits
	* correspond to zero speed (soft stop of motion) and positions beyond Low and High limits correspond MaxSpeed [i]
	* or -MaxSpeed [i] (see command SCTL), where i = 0 by default and can be changed with left/right buttons (see command SCTL).
	* If next speed in list is zero (both integer and microstep parts), the button press is ignored. First speed in list shouldn't be zero.
	* The DeadZone ranges are illustrated on the following picture.
	* !/attachments/download/5563/range25p.png!
	* The relationship between the deviation and the rate is exponential,
	* allowing no switching speed combine high mobility and accuracy. The following picture illustrates this:
	* !/attachments/download/3092/ExpJoystick.png!
	* The nonlinearity parameter is adjustable. Setting it to zero makes deviation/speed relation linear.
	* @param id an identifier of device
	* @param[out] joystick_settings structure contains joystick settings
	* \endenglish
	* \russian
	* Чтение настроек джойстика.
	* При отклонении джойстика более чем на DeadZone от центрального положения начинается движение со скоростью,
	* определяемой отклонением джойстика от DeadZone до 100% отклонения, причем отклонению DeadZone соответствует
	* нулевая скорость, а 100% отклонения соответствует MaxSpeed [i] (см. команду SCTL), где i=0, если предыдущим
	* использованием этого режима не было выбрано другое i.
	* Если следующая скорость в таблице скоростей нулевая (целая и микрошаговая части), то перехода на неё не происходит.
	* DeadZone вычисляется в десятых долях процента отклонения
	* от центра (JoyCenter) до правого или левого максимума. Расчёт DeadZone проиллюстрирован на графике: !/attachments/download/5563/range25p.png!
	* Зависимость между отклонением и скоростью экспоненциальная,
	* что позволяет без переключения режимов скорости сочетать высокую подвижность и точность. На графике ниже показан
	* пример экспоненциальной зависимости скорости и работы мертвой зоны.
	* !/attachments/download/3092/ExpJoystick.png!
	* Параметр нелинейнойсти можно менять. Нулевой параметр нелинейности соответствует линейной зависимости.
	* @param id идентификатор устройства
	* @param[out] joystick_settings структура, содержащая настройки джойстика
	* \endrussian
	*/
	result_t XIMC_API get_joystick_settings (device_t id, joystick_settings_t* joystick_settings);

/** 
	* \english
	* Set settings of control position(is only used with stepper motor).
	* When controlling the step motor with encoder (CTP_BASE 0) it is possible
	* to detect the loss of steps. The controller knows the number of steps per
	* revolution (GENG :: StepsPerRev) and the encoder resolution (GFBS :: IPT).
	* When the control (flag CTP_ENABLED), the controller stores the current position
	* in the footsteps of SM and the current position of the encoder. Further, at
	* each step of the position encoder is converted into steps and if the difference
	* is greater CTPMinError, a flag STATE_CTP_ERROR.
	* When controlling the step motor with speed sensor (CTP_BASE 1), the position is
	* controlled by him. The active edge of input clock controller stores the current
	* value of steps. Further, at each turn checks how many steps shifted. When a
	* mismatch CTPMinError a flag STATE_CTP_ERROR.
	* @param id an identifier of device
	* @param[in] ctp_settings structure contains settings of control position
	* \endenglish
	* \russian
	* Запись настроек контроля позиции(для шагового двигателя).
	* При управлении ШД с энкодером
	* (CTP_BASE 0) появляется возможность обнаруживать потерю шагов. Контроллер
	* знает кол-во шагов на оборот (GENG::StepsPerRev) и разрешение энкодера
	* (GFBS::IPT). При включении контроля (флаг CTP_ENABLED), контроллер запоминает
	* текущую позицию в шагах ШД и текущую позицию энкодера. Далее, на каждом шаге
	* позиция энкодера преобразовывается в шаги и если разница оказывается больше
	* CTPMinError, устанавливается флаг STATE_CTP_ERROR.
	* При управлении ШД с датчиком оборотов (CTP_BASE 1), позиция контролируется по нему.
	* По активному фронту на входе синхронизации контроллер запоминает текущее значение
	* шагов. Далее, при каждом обороте проверяет, на сколько шагов сместились. При
	* рассогласовании более CTPMinError устанавливается флаг STATE_CTP_ERROR.
	* @param id идентификатор устройства
	* @param[in] ctp_settings структура, содержащая настройки контроля позиции
	* \endrussian
	*/
	result_t XIMC_API set_ctp_settings (device_t id, const ctp_settings_t* ctp_settings);

/** 
	* \english
	* Read settings of control position(is only used with stepper motor).
	* When controlling the step motor with encoder (CTP_BASE 0) it is possible
	* to detect the loss of steps. The controller knows the number of steps per
	* revolution (GENG :: StepsPerRev) and the encoder resolution (GFBS :: IPT).
	* When the control (flag CTP_ENABLED), the controller stores the current position
	* in the footsteps of SM and the current position of the encoder. Further, at
	* each step of the position encoder is converted into steps and if the difference
	* is greater CTPMinError, a flag STATE_CTP_ERROR.
	* When controlling the step motor with speed sensor (CTP_BASE 1), the position is
	* controlled by him. The active edge of input clock controller stores the current
	* value of steps. Further, at each turn checks how many steps shifted. When a
	* mismatch CTPMinError a flag STATE_CTP_ERROR.
	* @param id an identifier of device
	* @param[out] ctp_settings structure contains settings of control position
	* \endenglish
	* \russian
	* Чтение настроек контроля позиции(для шагового двигателя).
	* При управлении ШД с энкодером
	* (CTP_BASE 0) появляется возможность обнаруживать потерю шагов. Контроллер
	* знает кол-во шагов на оборот (GENG::StepsPerRev) и разрешение энкодера
	* (GFBS::IPT). При включении контроля (флаг CTP_ENABLED), контроллер запоминает
	* текущую позицию в шагах ШД и текущую позицию энкодера. Далее, на каждом шаге
	* позиция энкодера преобразовывается в шаги и если разница оказывается больше
	* CTPMinError, устанавливается флаг STATE_CTP_ERROR.
	* При управлении ШД с датчиком оборотов (CTP_BASE 1), позиция контролируется по нему.
	* По активному фронту на входе синхронизации контроллер запоминает текущее значение
	* шагов. Далее, при каждом обороте проверяет, на сколько шагов сместились. При
	* рассогласовании более CTPMinError устанавливается флаг STATE_CTP_ERROR.
	* @param id идентификатор устройства
	* @param[out] ctp_settings структура, содержащая настройки контроля позиции
	* \endrussian
	*/
	result_t XIMC_API get_ctp_settings (device_t id, ctp_settings_t* ctp_settings);

/** 
	* \english
	* Set UART settings.
	* This function send structure with UART settings to controller's memory.
	* @see uart_settings_t
	* @param Speed UART speed
	* @param[in] uart_settings UART settings
	* \endenglish
	* \russian
	*  Команда записи настроек UART.
	* Эта функция записывает структуру настроек UART в память контроллера.
	* @see uart_settings_t
	* @param Speed Cкорость UART
	* @param[in] uart_settings настройки UART
	* \endrussian
	*/
	result_t XIMC_API set_uart_settings (device_t id, const uart_settings_t* uart_settings);

/** 
	* \english
	* Read UART settings.
	* This function fill structure with UART settings.
	* @see uart_settings_t
	* @param Speed UART speed
	* @param[out] uart_settings UART settings
	* \endenglish
	* \russian
	* Команда чтения настроек UART.
	* Эта функция заполняет структуру настроек UART.
	* @see uart_settings_t
	* @param Speed Cкорость UART
	* @param[out] uart_settings настройки UART
	* \endrussian
	*/
	result_t XIMC_API get_uart_settings (device_t id, uart_settings_t* uart_settings);

/** 
	* \english
	* Set calibration settings.
	* This function send structure with calibration settings to controller's memory.
	* @see calibration_settings_t
	* @param id an identifier of device
	* @param[in] calibration_settings calibration settings
	* \endenglish
	* \russian
	* Команда записи калибровочных коэффициентов.
	* Эта функция записывает структуру калибровочных коэффициентов в память контроллера.
	* @see calibration_settings_t
	* @param id идентификатор устройства
	* @param[in] calibration_settings калибровочные коэффициенты
	* \endrussian
	*/
	result_t XIMC_API set_calibration_settings (device_t id, const calibration_settings_t* calibration_settings);

/** 
	* \english
	* Read calibration settings.
	* This function fill structure with calibration settings.
	* @see calibration_settings_t
	* @param id an identifier of device
	* @param[out] calibration_settings calibration settings
	* \endenglish
	* \russian
	* Команда чтения калибровочных коэффициентов.
	* Эта функция заполняет структуру калибровочных коэффициентов.
	* @see calibration_settings_t
	* @param id идентификатор устройства
	* @param[out] calibration_settings калибровочные коэффициенты
	* \endrussian
	*/
	result_t XIMC_API get_calibration_settings (device_t id, calibration_settings_t* calibration_settings);

/** 
	* \english
	* Write user controller name and flags of setting from FRAM.
	* @param id an identifier of device
	* @param[in] controller_name structure contains previously set user controller name
	* \endenglish
	* \russian
	* Запись пользовательского имени контроллера и настроек в FRAM.
	* @param id идентификатор устройства
	* @param[in] controller_information структура, содержащая информацию о контроллере
	* \endrussian
	*/
	result_t XIMC_API set_controller_name (device_t id, const controller_name_t* controller_name);

/** 
	* \english
	* Read user controller name and flags of setting from FRAM.
	* @param id an identifier of device
	* @param[out] controller_name structure contains previously set user controller name
	* \endenglish
	* \russian
	* Чтение пользовательского имени контроллера и настроек из FRAM.
	* @param id идентификатор устройства
	* @param[out] controller_name структура, содержащая установленное пользовательское имя контроллера и флаги настроек
	* \endrussian
	*/
	result_t XIMC_API get_controller_name (device_t id, controller_name_t* controller_name);

/** 
	* \english
	* Write userdata into FRAM.
	* @param id an identifier of device
	* @param[in] nonvolatile_memory structure contains previously set userdata
	* \endenglish
	* \russian
	* Запись пользовательских данных во FRAM.
	* @param id идентификатор устройства
	* @param[in] nonvolatile_memory структура, содержащая установленные пользовательские данные
	* \endrussian
	*/
	result_t XIMC_API set_nonvolatile_memory (device_t id, const nonvolatile_memory_t* nonvolatile_memory);

/** 
	* \english
	* Read userdata from FRAM.
	* @param id an identifier of device
	* @param[out] nonvolatile_memory structure contains previously set userdata
	* \endenglish
	* \russian
	* Чтение пользовательских данных из FRAM.
	* @param id идентификатор устройства
	* @param[out] nonvolatile_memory структура, содержащая установленные пользовательские данные
	* \endrussian
	*/
	result_t XIMC_API get_nonvolatile_memory (device_t id, nonvolatile_memory_t* nonvolatile_memory);

/**  
	* \english
	* Set electromechanical coefficients.
	* The settings are different for different stepper motors.
	* Please download the new settings when you change the motor.
	* @see get_emf_settings
	* @param id an identifier of device
	* @param[in] emf_settings EMF settings
	* \endenglish
	* \russian
	* Запись электромеханических настроек шагового двигателя. 
	* Настройки различны для разных двигателей.
	* Пожалуйста, загружайте новые настройки, когда вы меняете мотор.
	* @see get_emf_settings
	* @param id идентификатор устройства
	* @param[in] emf_settings настройки EMF
	* \endrussian
	*/
	result_t XIMC_API set_emf_settings (device_t id, const emf_settings_t* emf_settings);

/**  
	* \english
	* Read electromechanical settings.
	* The settings are different for different stepper motors.
	* @see set_emf_settings
	* @param id an identifier of device
	* @param[out] emf_settings EMF settings
	* \endenglish
	* \russian
	* Чтение электромеханических настроек шагового двигателя. 
	* Настройки различны для разных двигателей.
	* @see set_emf_settings
	* @param id идентификатор устройства
	* @param[out] emf_settings настройки EMF
	* \endrussian
	*/
	result_t XIMC_API get_emf_settings (device_t id, emf_settings_t* emf_settings);

/**  
	* \english
	* Set engine advansed settings.
	* @see get_engine_advansed_setup
	* @param id an identifier of device
	* @param[in] engine_advansed_setup EAS settings
	* \endenglish
	* \russian
	* Запись расширенных настроек. 
	* @see get_engine_advansed_setup
	* @param id идентификатор устройства
	* @param[in] engine_advansed_setup настройки EAS
	* \endrussian
	*/
	result_t XIMC_API set_engine_advansed_setup (device_t id, const engine_advansed_setup_t* engine_advansed_setup);

/**  
	* \english
	* Read engine advansed settings.
	* @see set_engine_advansed_setup
	* @param id an identifier of device
	* @param[out] engine_advansed_setup EAS settings
	* \endenglish
	* \russian
	* Чтение расширенных настроек. 
	* @see set_engine_advansed_setup
	* @param id идентификатор устройства
	* @param[out] engine_advansed_setup настройки EAS
	* \endrussian
	*/
	result_t XIMC_API get_engine_advansed_setup (device_t id, engine_advansed_setup_t* engine_advansed_setup);

/**  
	* \english
	* Set extended settings.
	* @see get_extended_settings
	* @param id an identifier of device
	* @param[in] extended_settings EST settings
	* \endenglish
	* \russian
	* Запись расширенных настроек. 
	* @see get_extended_settings
	* @param id идентификатор устройства
	* @param[in] extended_settings настройки EST
	* \endrussian
	*/
	result_t XIMC_API set_extended_settings (device_t id, const extended_settings_t* extended_settings);

/**  
	* \english
	* Read extended settings.
	* @see set_extended_settings 
	* @param id an identifier of device
	* @param[out] extended_settings EST settings
	* \endenglish
	* \russian
	* Чтение расширенных настроек. 
	* @see set_extended_settings
	* @param id идентификатор устройства
	* @param[out] extended_settings настройки EST
	* \endrussian
	*/
	result_t XIMC_API get_extended_settings (device_t id, extended_settings_t* extended_settings);


//@}

/**
	* \english
	* @name Group of commands movement control
	*
	* \endenglish
	* \russian
	* @name Группа команд управления движением
	*
	* \endrussian
	*/

//@{

/**  
	* \english
	* Immediately stop the engine, the transition to the STOP, mode
	* key BREAK (winding short-circuited), the regime "retention" is
	* deactivated for DC motors, keeping current in the windings for
	* stepper motors (with Power management settings).
	* When this command is called, the ALARM flag is reset.
	* @param id an identifier of device
	* \endenglish
	* \russian
	* Немедленная остановка двигателя, переход в состояние STOP,
	* ключи в режиме BREAK (обмотки накоротко замкнуты), режим
	* "удержания" дезактивируется для DC двигателей, удержание тока
	* в обмотках для шаговых двигателей (с учётом Power management
	* настроек).
	* При вызове этой команды сбрасывается флаг ALARM.
	* @param id идентификатор устройства
	* \endrussian
	*/
	result_t XIMC_API command_stop (device_t id);

/** 
	* \english
	* Immediately power off motor regardless its state. Shouldn't be used
	* during motion as the motor could be power on again automatically to continue movement.
	* The command is designed for manual motor power off.
	* When automatic power off after stop is required, use power management system.
	* @param id an identifier of device
	* \endenglish
	* \russian
	* Немедленное отключение питания двигателя вне зависимости от его состояния.
	* Команда предначена для ручного управления питанием двигателя.
	* Не следует использовать эту команду для отключения двигателя во время движения, так как питание может снова включиться для завершения движения.
	* Для автоматического управления питанием двигателя и его отключении после остановки следует использовать систему управления электропитанием.
	* @param id идентификатор устройства
	* \endrussian
	* @see get_power_settings
	* @see set_power_settings
	*/
	result_t XIMC_API command_power_off (device_t id);

/** 
	* \english
	* Upon receiving the command "move" the engine starts to move with pre-set parameters (speed, acceleration, retention),
	* to the point specified to the Position, uPosition. For stepper motor uPosition
	* sets the microstep, for DC motor this field is not used.
	* @param id an identifier of device
	* @param Position position to move.
	* @param uPosition part of the position to move, microsteps. Microstep size and the range of valid values for this field depend on selected step division mode (see MicrostepMode field in engine_settings).
	* \endenglish
	* \russian
	* При получении команды "move" двигатель начинает перемещаться (если не используется
	* режим "ТТЛСинхроВхода"), с заранее установленными параметрами (скорость, ускорение,
	* удержание), к точке указанной в полях Position, uPosition. Для шагового мотора
	* uPosition задает значение микрошага, для DC мотора это поле не используется.
	* @param id идентификатор устройства
	* @param Position заданная позиция.
	* @param uPosition часть позиции в микрошагах. Величина микрошага и диапазон допустимых значений для данного поля зависят от выбранного режима деления шага (см. поле MicrostepMode в engine_settings).	
	* \endrussian
	*/
	result_t XIMC_API command_move (device_t id, int Position, int uPosition);

/** 
	* \english
	* Move to position which use user units.
	* Upon receiving the command "move" the engine starts to move with pre-set parameters (speed, acceleration, retention),
	* to the point specified to the Position.
	* @param id an identifier of device
	* @param Position position to move.
	* @param calibration user unit settings
	* 
	* \note
	* The parameter Position is adjusted by the correction table.
	*
	* \endenglish
	* \russian
	* Перемещение в позицию  с использованием пользовательских единиц.
	* При получении команды "move" двигатель начинает перемещаться (если не используется
	* режим "ТТЛСинхроВхода"), с заранее установленными параметрами (скорость, ускорение,
	* удержание), к точке указанной в поле Position. 
	* @param id идентификатор устройства
	* @param Position позиция для перемещения
	* @param calibration настройки пользовательских единиц
	*
	* \note
	* Параметр Position корректируется таблицей коррекции.
	*
	* \endrussian
	*/
	result_t XIMC_API command_move_calb (device_t id, float Position, const calibration_t* calibration);

/** 
	* \english
	* Move to offset.
	* Upon receiving the command "movr" engine starts to move with pre-set parameters (speed, acceleration,
	* hold), left or right (depending on the sign of DeltaPosition) by the number of
	* pulses specified in the fields DeltaPosition, uDeltaPosition. For stepper motor
	* uDeltaPosition sets the microstep, for DC motor this field is not used.
	* @param DeltaPosition shift from initial position.
	* @param uDeltaPosition part of the offset shift, microsteps. Microstep size and the range of valid values for this field depend on selected step division mode (see MicrostepMode field in engine_settings).
	* @param id an identifier of device
	* \endenglish
	* \russian
	* Перемещение на заданное смещение.
	* При получении команды "movr" двигатель начинает смещаться (если не используется
	* режим "ТТЛСинхроВхода"), с заранее установленными параметрами (скорость, ускорение,
	* удержание), влево или вправо (зависит от знака DeltaPosition) на количество
	* импульсов указанное в полях DeltaPosition, uDeltaPosition. Для шагового мотора
	* uDeltaPosition задает значение микрошага, для DC мотора это поле не используется.
	* @param DeltaPosition смещение.
	* @param uDeltaPosition часть смещения в микрошагах. Величина микрошага и диапазон допустимых значений для данного поля зависят от выбранного режима деления шага (см. поле MicrostepMode в engine_settings).
	* @param id идентификатор устройства
	* \endrussian
	*/
	result_t XIMC_API command_movr (device_t id, int DeltaPosition, int uDeltaPosition);

/** 
	* \english
	* Move to offset using user units.
	* Upon receiving the command "movr" engine starts to move with pre-set parameters (speed, acceleration,
	* hold), left or right (depending on the sign of DeltaPosition) the distance specified in the field
	* DeltaPosition.
	* @param DeltaPosition shift from initial position.
	* @param id an identifier of device
	* @param calibration user unit settings 
	*
	* \note
	* The end coordinate is calculated using DeltaPosition, is adjusted by the correction table.
	* To calculate coordinates correctly, when using a correction table, you do not need to execute movr commands in batches.
	*
	* \endenglish
	* \russian
	* Перемещение на заданное смещение с использованием пользовательских единиц.
	* При получении команды "movr" двигатель начинает смещаться (если не используется
	* режим "ТТЛСинхроВхода"), с заранее установленными параметрами (скорость, ускорение,
	* удержание), влево или вправо (зависит от знака DeltaPosition) на расстояние
	* указанное в поле DeltaPosition. 
	* @param DeltaPosition смещение.
	* @param id идентификатор устройства
	* @param calibration настройки пользовательских единиц
	*
	* \note
	* Конечная координата вычисляемая с помощью DeltaPosition, корректируется таблицей коррекции.
	* Для корректного рассчета координат, при использовании корректирующей таблицы, не нужно выполнять команды movr пакетами.
	*
	* \endrussian
	*/
	result_t XIMC_API command_movr_calb (device_t id, float DeltaPosition, const calibration_t* calibration);

/** 
	* \english
	* The positive direction is to the right. A value of zero reverses the direction of the
	* direction of the flag, the set speed.
	* Restriction imposed by the trailer, act the same, except that the limit switch contact
	* does not stop. Limit the maximum speed, acceleration and deceleration function.
	* 1) moves the motor according to the speed FastHome, uFastHome and flag HOME_DIR_FAST until
	* limit switch, if the flag is set HOME_STOP_ENDS, until the signal from the input synchronization if
	* the flag HOME_STOP_SYNC (as accurately as possible is important to catch the moment of operation limit switch)
	* or until the signal is received from the speed sensor, if the flag HOME_STOP_REV_SN
	* 2) then moves according to the speed SlowHome, uSlowHome and flag HOME_DIR_SLOW until
	* signal from the clock input, if the flag HOME_MV_SEC. If the flag HOME_MV_SEC reset
	* skip this paragraph.
	* 3) then move the motor according to the speed FastHome, uFastHome and flag HOME_DIR_SLOW a distance
	* HomeDelta, uHomeDelta.
	* description of flags and variable see in description for commands GHOM/SHOM
	* @param id an identifier of device
	* \endenglish
	* \russian
	* Поля скоростей знаковые. Положительное направление это вправо. Нулевое значение флага
	* направления инвертирует направление, заданное скоростью.
	* Ограничение, накладываемые концевиками, действуют так же, за исключением того, что касание
	* концевика не приводит к остановке. Ограничения максимальной скорости, ускорения и замедления действуют.
	* 1) Двигает мотор согласно скоростям FastHome, uFastHome и флагу HOME_DIR_FAST до достижения
	* концевика, если флаг HOME_STOP_ENDS установлен, до достижения сигнала с входа синхронизации, если
	* установлен флаг HOME_STOP_SYNC (важно как можно точнее поймать момент срабатывания концевика)
	* или  до поступления сигнала с датчика оборотов, если установлен флаг HOME_STOP_REV_SN
	* 2) далее двигает согласно скоростям SlowHome, uSlowHome и флагу HOME_DIR_SLOW до достижения
	* сигнала с входа синхронизации, если установлен флаг HOME_MV_SEC. Если флаг HOME_MV_SEC сброшен,
	* пропускаем этот пункт.
	* 3) далее двигает мотор согласно скоростям FastHome, uFastHome и флагу HOME_DIR_SLOW на расстояние
	* HomeDelta, uHomeDelta.
	* Описание флагов и переменных см. описание команд GHOM/SHOM
	* @param id идентификатор устройства
	* \endrussian
	@see home_settings_t
	@see get_home_settings
	@see set_home_settings
	*/
	result_t XIMC_API command_home (device_t id);

/** 
	* \english
	* Start continous moving to the left.
	* @param id an identifier of device
	* \endenglish
	* \russian
	* При получении команды "left" двигатель начинает смещаться, с заранее установленными параметрами (скорость, ускорение), влево.
	* @param id идентификатор устройства
	* \endrussian
	*/
	result_t XIMC_API command_left (device_t id);

/** 
	* \english
	* Start continous moving to the right.
	* @param id an identifier of device
	* \endenglish
	* \russian
	* При получении команды "rigt" двигатель начинает смещаться, с заранее установленными параметрами (скорость, ускорение), вправо.
	* @param id идентификатор устройства
	* \endrussian
	*/
	result_t XIMC_API command_right (device_t id);

/** 
	* \english
	* Upon receiving the command "loft" the engine is shifted from the current
	* point to a distance GENG :: Antiplay, then move to the same point.
	* @param id an identifier of device
	* \endenglish
	* \russian
	* При получении команды "loft" двигатель смещается из текущей точки на
	* расстояние GENG::Antiplay, затем двигается в ту же точку.
	* @param id идентификатор устройства
	* \endrussian
	*/
	result_t XIMC_API command_loft (device_t id);

/** 
	* \english
	* Soft stop engine. The motor stops with deceleration speed.
	* @param id an identifier of device
	* \endenglish
	* \russian
	* Плавная остановка. Двигатель останавливается с ускорением замедления.
	* @param id идентификатор устройства
	* \endrussian
	*/
	result_t XIMC_API command_sstp (device_t id);

/** 
	* \english
	* Reads the value position in steps and micro for stepper motor and encoder steps
	* all engines.
	* @param id an identifier of device
	* @param[out] the_get_position structure contains move settings: speed, acceleration, deceleration etc.
	* \endenglish
	* \russian
	* Считывает значение положения в шагах и микрошагах для шагового двигателя и в шагах энкодера
	* всех двигателей.
	* @param id идентификатор устройства
	* @param[out] position структура, содержащая настройки движения: скорость, ускорение, и т.д.
	* \endrussian
	*/
	result_t XIMC_API get_position (device_t id, get_position_t* the_get_position);

/** 
	* \english
	* Reads position value in user units for stepper motor and encoder steps
	* all engines.
	* @param id an identifier of device
	* @param[out] the_get_position_calb structure contains move settings: speed, acceleration, deceleration etc.
	* @param calibration user unit settings
	* 
	* \note
	* Attention! Some parameters of the the_get_position_calb structure are corrected by the coordinate correction table.
	*
	* \endenglish
	* \russian
	* Считывает значение положения в пользовательских единицах для шагового двигателя и в шагах энкодера
	* всех двигателей.
	* @param id идентификатор устройства
	* @param[out] the_get_position_calb структура, содержащая настройки движения: скорость, ускорение, и т.д.
	* @param calibration настройки пользовательских единиц
	*
	* \note
	* Внимание! Некоторые параметры структуры the_get_position_calb корректируются таблицей коррекции координат.  
	*
	* \endrussian
	*/
	result_t XIMC_API get_position_calb (device_t id, get_position_calb_t* the_get_position_calb, const calibration_t* calibration);

/** 
	* \english
	* Sets any position value in steps and micro for stepper motor
	* and encoder steps of all engines. It means, that changing main
	* indicator of position.
	* @param id an identifier of device
	* @param[out] the_set_position structure contains move settings: speed, acceleration, deceleration etc.
	* \endenglish
	* \russian
	* Устанавливает произвольное значение положения в шагах и
	* микрошагах для шагового двигателя и в шагах энкодера всех
	* двигателей. То есть меняется основной показатель положения.
	* @param id идентификатор устройства
	* @param[out] position структура, содержащая настройки движения: скорость, ускорение, и т.д.
	* \endrussian
	*/
	result_t XIMC_API set_position (device_t id, const set_position_t* the_set_position);

/** 
	* \english
	* Sets any position value
	* and encoder value of all engines which use user units. It means, that changing main
	* indicator of position.
	* @param id an identifier of device
	* @param[out] the_set_position_calb structure contains move settings: speed, acceleration, deceleration etc.
	* @param calibration user unit settings
	* \endenglish
	* \russian
	* Устанавливает произвольное значение положения и значение энкодера всех
	* двигателей с использованием пользовательских единиц. То есть меняется основной показатель положения.
	* @param id идентификатор устройства
	* @param[out] the_set_position_calb структура, содержащая настройки движения: скорость, ускорение, и т.д.
	* @param calibration настройки пользовательских единиц
	* \endrussian
	*/
	result_t XIMC_API set_position_calb (device_t id, const set_position_calb_t* the_set_position_calb, const calibration_t* calibration);

/** 
	* \english
	* Sets the current position and the position in which the traffic moves by the move command
	* and movr zero for all cases, except for movement to the target position. In the latter case,
	* set the zero current position and the target position counted so that the absolute position
	* of the destination is the same. That is, if we were at 400 and moved to 500, then the command
	* Zero makes the current position of 0, and the position of the destination - 100. Does not
	* change the mode of movement that is if the motion is carried, it continues, and if the engine
	* is in the "hold", the type of retention remains.
	* @param id an identifier of device
	* \endenglish
	* \russian
	* Устанавливает текущую позицию и позицию в которую осуществляется движение по командам
	* move и movr равными нулю для всех случаев, кроме движения к позиции назначения.
	* В последнем случае установить нулём текущую позицию, а позицию назначения пересчитать так,
	* что в абсолютном положении точка назначения не меняется. То есть если мы находились в точке
	* 400 и двигались к 500, то команда Zero делает текущую позицию 0, а позицию назначения - 100.
	* Не изменяет режим движения т.е. если движение осуществлялось, то оно продолжается; если
	* мотор находился в режиме "удержания", то тип удержания сохраняется.
	* @param id идентификатор устройства
	* \endrussian
	*/
	result_t XIMC_API command_zero (device_t id);


//@}

/**
	* \english
	* @name Group of commands to save and load settings
	*
	* \endenglish
	* \russian
	* @name Группа команд сохранения и загрузки настроек
	*
	* \endrussian
	*/

//@{

/** 
	* \english
	* Save all settings from controller's RAM to controller's flash memory, replacing previous data in controller's flash memory.
	* @param id an identifier of device
	* \endenglish
	* \russian
	* При получении команды контроллер выполняет операцию сохранения текущих настроек во встроенную энергонезависимую память контроллера.
	* @param id идентификатор устройства
	* \endrussian
	*/
	result_t XIMC_API command_save_settings (device_t id);

/** 
	* \english
	* Read all settings from controller's flash memory to controller's RAM, replacing previous data in controller's RAM.
	* @param id an identifier of device
	* \endenglish
	* \russian
	* Чтение всех настроек контроллера из flash памяти в оперативную, заменяя текущие настройки.
	* @param id идентификатор устройства
	* \endrussian
	*/
	result_t XIMC_API command_read_settings (device_t id);

/** 
	* \english
	* Save important settings (calibration coefficients and etc.) from controller's RAM to controller's flash memory, replacing previous data in controller's flash memory.
	* @param id an identifier of device
	* \endenglish
	* \russian
	* При получении команды контроллер выполняет операцию сохранения важных настроек (калибровочные коэффициенты и т.п.) во встроенную энергонезависимую память контроллера.
	* @param id идентификатор устройства
	* \endrussian
	*/
	result_t XIMC_API command_save_robust_settings (device_t id);

/** 
	* \english
	* Read important settings (calibration coefficients and etc.) from controller's flash memory to controller's RAM, replacing previous data in controller's RAM.
	* @param id an identifier of device
	* \endenglish
	* \russian
	* Чтение важных настроек (калибровочные коэффициенты и т.п.) контроллера из flash памяти в оперативную, заменяя текущие настройки.
	* @param id идентификатор устройства
	* \endrussian
	*/
	result_t XIMC_API command_read_robust_settings (device_t id);

/** 
	* \english
	* Save settings from controller's RAM to stage's EEPROM memory, which spontaneity connected to stage and it isn`t change without it mechanical reconstruction.
	* Can be used by manufacturer only.
	* @param id an identifier of device
	* \endenglish
	* \russian
	* Запись настроек контроллера в EEPROM память позиционера, которые непосредственно связаны с позиционером и не меняются без его механической переделки.
	* Функция должна использоваться только производителем.
	* @param id идентификатор устройства
	* \endrussian
	*/
	result_t XIMC_API command_eesave_settings (device_t id);

/** 
	* \english
	* Read settings from controller's RAM to stage's EEPROM memory, which spontaneity connected to stage and it isn`t change without it mechanical reconstruction.
	* @param id an identifier of device
	* \endenglish
	* \russian
	* Чтение настроек контроллера из EEPROM памяти позиционера, которые непосредственно связаны с позиционером и не меняются без его механической переделки.
	* Эта операция также автоматически выполняется при подключении позиционера с EEPROM памятью. Функция должна использоваться только производителем.
	* @param id идентификатор устройства
	* \endrussian
	*/
	result_t XIMC_API command_eeread_settings (device_t id);

/** 
  * \english
  * Start measurements and buffering of speed, following error.
  * @param id an identifier of device
  * \endenglish
  * \russian
  * Начать измерения и буферизацию скорости, ошибки следования.
  * @param id идентификатор устройства
  * \endrussian
  */
	result_t XIMC_API command_start_measurements (device_t id);

/** 
  * \english
  * A command to read the data buffer to build a speed graph and a sequence error. Filling the buffer starts with the command "start_measurements".
  * The buffer holds 25 points, the points are taken with a period of 1 ms. To create a robust system, read data every 20 ms,
  * if the buffer is completely full, then it is recommended to repeat the readings every 5 ms until the buffer again becomes filled with 20 points.
  * @see measurements_t
  * @param id an identifier of device
  * @param[out] measurements structure with buffer and its length.
  * \endenglish
  * \russian
  * Команда чтения буфера данных для построения графиков скорости и ошибки следования. Заполнение буфера начинается по команде "start_measurements".
  * Буффер вмещает 25 точек, точки снимаются с периодом 1 мс. Для создания устойчивой системы следует считывать данные каждые 20 мс, если буффер
  * полностью заполнен, то рекомендуется повторять считывания каждые 5 мс до момента пока буффер вновь не станет заполнен 20-ю точками.
  * @see measurements_t
  * @param id идентификатор устройства
  * @param[out] measurements структура с буфером и его длинной.
  * \endrussian
  */
	result_t XIMC_API get_measurements (device_t id, measurements_t* measurements);

/** 
	* \english
	* Return device electrical parameters, useful for charts.
	* Useful function that fill structure with snapshot of controller voltages and currents.
	* @see chart_data_t
	* @param id an identifier of device
	* @param[out] chart_data structure with snapshot of controller parameters.
	* \endenglish
	* \russian
	* Команда чтения состояния обмоток и других не часто используемых данных. Предназначена
	* в первую очередь для получения данных для построения графиков в паре с командой GETS.
	* @see chart_data_t
	* @param id идентификатор устройства
	* @param[out] chart_data структура chart_data.
	* \endrussian
	*/
	result_t XIMC_API get_chart_data (device_t id, chart_data_t* chart_data);

/** 
	* \english
	* Read device serial number.
	* @param id an identifier of device
	* @param[out] SerialNumber serial number
	* \endenglish
	* \russian
	* Чтение серийного номера контроллера.
	* @param id идентификатор устройства
	* @param[out] SerialNumber серийный номер контроллера
	* \endrussian
	*/
	result_t XIMC_API get_serial_number (device_t id, unsigned int* SerialNumber);

/** 
	* \english
	* Read controller's firmware version.
	* @param id an identifier of device
	* @param[out] Major major version
	* @param[out] Minor minor version
	* @param[out] Release release version
	* \endenglish
	* \russian
	* Чтение номера версии прошивки контроллера.
	* @param id идентификатор устройства
	* @param[out] Major номер основной версии
	* @param[out] Minor номер дополнительной версии
	* @param[out] Release номер релиза
	* \endrussian
	*/
	result_t XIMC_API get_firmware_version (device_t id, unsigned int* Major, unsigned int* Minor, unsigned int* Release);

/** 
	* \english
	* Command puts the controller to update the firmware.
	* After receiving this command, the firmware board sets a flag (for loader), sends echo reply and restarts the controller.
	* \endenglish
	* \russian
	* Команда переводит контроллер в режим обновления прошивки.
	* Получив такую команду, прошивка платы устанавливает флаг (для загрузчика), отправляет эхо-ответ и перезагружает контроллер.
	* \endrussian
	*/
	result_t XIMC_API service_command_updf (device_t id);


//@}

/**
	* \english
	* @name Service commands
	*
	* \endenglish
	* \russian
	* @name Группа сервисных команд
	*
	* \endrussian
	*/

//@{

/** 
	* \english
	* Write device serial number and hardware version to controller's flash memory.
	* Along with the new serial number and hardware version a "Key" is transmitted.
	* The SN and hardware version are changed and saved when keys match.
	* Can be used by manufacturer only.
	* @param id an identifier of device
	* @param[in] serial_number structure contains new serial number and secret key.
	* \endenglish
	* \russian
	* Запись серийного номера и версии железа во flash память контроллера.
	* Вместе с новым серийным номером и версией железа передаётся "Ключ",
	* только при совпадении которого происходит изменение и сохранение.
	* Функция используется только производителем.
	* @param id идентификатор устройства
	* @param[in] serial_number структура, содержащая серийный номер, версию железа и ключ.
	* \endrussian
	*/
	result_t XIMC_API set_serial_number (device_t id, const serial_number_t* serial_number);

/** 
	* \english
	* Read analog data structure that contains raw analog data from ADC embedded on board.
	* This function used for device testing and deep recalibraton by manufacturer only.
	* @param id an identifier of device
	* @param[out] analog_data analog data coefficients
	* \endenglish
	* \russian
	* Чтение аналоговых данных, содержащих данные с АЦП и нормированные значения величин.
	* Эта функция используется для тестирования и калибровки устройства.
	* @param id идентификатор устройства
	* @param[out] analog_data аналоговые данные
	* \endrussian
	*/
	result_t XIMC_API get_analog_data (device_t id, analog_data_t* analog_data);

/** 
	* \english
	* Read data from firmware for debug purpose.
	* Its use depends on context, firmware version and previous history.
	* @param id an identifier of device
	* @param[out] debug_read Debug data.
	* \endenglish
	* \russian
	* Чтение данных из прошивки для отладки и поиска неисправностей.
	* Получаемые данные зависят от версии прошивки, истории и контекста использования.
	* @param id идентификатор устройства
	* @param[out] debug_read Данные для отладки.
	* \endrussian
	*/
	result_t XIMC_API get_debug_read (device_t id, debug_read_t* debug_read);

/** 
	* \english
	* Write data to firmware for debug purpose.
	* @param id an identifier of device
	* @param[in] debug_write Debug data.
	* \endenglish
	* \russian
	* Запись данных в прошивку для отладки и поиска неисправностей.
	* @param id идентификатор устройства
	* @param[in] debug_write Данные для отладки.
	* \endrussian
	*/
	result_t XIMC_API set_debug_write (device_t id, const debug_write_t* debug_write);


//@}

/**
	* \english
	* @name Group of commands to work with EEPROM
	*
	* \endenglish
	* \russian
	* @name Группа команд работы с EEPROM подвижки
	*
	* \endrussian
	*/

//@{

/** 
	* \english
	* Write user stage name from EEPROM.
	* @param id an identifier of device
	* @param[in] stage_name structure contains previously set user stage name
	* \endenglish
	* \russian
	* Запись пользовательского имени подвижки в EEPROM.
	* @param id идентификатор устройства
	* @param[in] stage_name структура, содержащая установленное пользовательское имя позиционера
	* \endrussian
	*/
	result_t XIMC_API set_stage_name (device_t id, const stage_name_t* stage_name);

/** 
	* \english
	* Read user stage name from EEPROM.
	* @param id an identifier of device
	* @param[out] stage_name structure contains previously set user stage name
	* \endenglish
	* \russian
	* Чтение пользовательского имени подвижки из EEPROM.
	* @param id идентификатор устройства
	* @param[out] stage_name структура, содержащая установленное пользовательское имя позиционера
	* \endrussian
	*/
	result_t XIMC_API get_stage_name (device_t id, stage_name_t* stage_name);

/** 
	* \english
	* Set stage information to EEPROM.
	* Can be used by manufacturer only.
	* @param id an identifier of device
	* @param[in] stage_information structure contains stage information
	* \endenglish
	* \russian
	* Запись информации о позиционере в EEPROM.
	* Функция должна использоваться только производителем.
	* @param id идентификатор устройства
	* @param[in] stage_information структура, содержащая информацию о позиционере
	* \endrussian
	*/
	result_t XIMC_API set_stage_information (device_t id, const stage_information_t* stage_information);

/** 
	* \english
	* Read stage information from EEPROM.
	* @param id an identifier of device
	* @param[out] stage_information structure contains stage information
	* \endenglish
	* \russian
	* Чтение информации о позиционере из EEPROM.
	* @param id идентификатор устройства
	* @param[out] stage_information структура, содержащая информацию о позиционере
	* \endrussian
	*/
	result_t XIMC_API get_stage_information (device_t id, stage_information_t* stage_information);

/** 
	* \english
	* Set stage settings to EEPROM.
	* Can be used by manufacturer only
	* @param id an identifier of device
	* @param[in] stage_settings structure contains stage settings
	* \endenglish
	* \russian
	* Запись настроек позиционера в EEPROM.
	* Функция должна использоваться только производителем.
	* @param id идентификатор устройства
	* @param[in] stage_settings структура, содержащая настройки позиционера
	* \endrussian
	*/
	result_t XIMC_API set_stage_settings (device_t id, const stage_settings_t* stage_settings);

/**  
	* \english
	* Read stage settings from EEPROM.
	* @param id an identifier of device
	* @param[out] stage_settings structure contains stage settings
	* \endenglish
	* \russian
	* Чтение настроек позиционера из EEPROM.
	* @param id идентификатор устройства
	* @param[out] stage_settings структура, содержащая настройки позиционера
	* \endrussian
	*/
	result_t XIMC_API get_stage_settings (device_t id, stage_settings_t* stage_settings);

/** 
	* \english
	* Set motor information to EEPROM.
	* Can be used by manufacturer only.
	* @param id an identifier of device
	* @param[in] motor_information structure contains motor information
	* \endenglish
	* \russian
	* Запись информации о двигателе в EEPROM.
	* Функция должна использоваться только производителем.
	* @param id идентификатор устройства
	* @param[in] motor_information структура, содержащая информацию о двигателе
	* \endrussian
	*/
	result_t XIMC_API set_motor_information (device_t id, const motor_information_t* motor_information);

/**  
	* \english
	* Read motor information from EEPROM.
	* @param id an identifier of device
	* @param[out] motor_information structure contains motor information
	* \endenglish
	* \russian
	* Чтение информации о двигателе из EEPROM.
	* @param id идентификатор устройства
	* @param[out] motor_information структура, содержащая информацию о двигателе
	* \endrussian
	*/
	result_t XIMC_API get_motor_information (device_t id, motor_information_t* motor_information);

/** 
	* \english
	* Set motor settings to EEPROM.
	* Can be used by manufacturer only.
	* @param id an identifier of device
	* @param[in] motor_settings structure contains motor information
	* \endenglish
	* \russian
	* Запись настроек двигателя в EEPROM.
	* Функция должна использоваться только производителем.
	* @param id идентификатор устройства
	* @param[in] motor_settings структура, содержащая настройки двигателя
	* \endrussian
	*/
	result_t XIMC_API set_motor_settings (device_t id, const motor_settings_t* motor_settings);

/**  
	* \english
	* Read motor settings from EEPROM.
	* @param id an identifier of device
	* @param[out] motor_settings structure contains motor settings
	* \endenglish
	* \russian
	* Чтение настроек двигателя из EEPROM.
	* @param id идентификатор устройства
	* @param[out] motor_settings структура, содержащая настройки двигателя
	* \endrussian
	*/
	result_t XIMC_API get_motor_settings (device_t id, motor_settings_t* motor_settings);

/** 
	* \english
	* Set encoder information to EEPROM.
	* Can be used by manufacturer only.
	* @param id an identifier of device
	* @param[in] encoder_information structure contains information about encoder
	* \endenglish
	* \russian
	* Запись информации об энкодере в EEPROM.
	* Функция должна использоваться только производителем.
	* @param id идентификатор устройства
	* @param[in] encoder_information структура, содержащая информацию об энкодере
	* \endrussian
	*/
	result_t XIMC_API set_encoder_information (device_t id, const encoder_information_t* encoder_information);

/** 
	* \english
	* Read encoder information from EEPROM.
	* @param id an identifier of device
	* @param[out] encoder_information structure contains information about encoder
	* \endenglish
	* \russian
	* Чтение информации об энкодере из EEPROM.
	* @param id идентификатор устройства
	* @param[out] encoder_information структура, содержащая информацию об энкодере
	* \endrussian
	*/
	result_t XIMC_API get_encoder_information (device_t id, encoder_information_t* encoder_information);

/** 
	* \english
	* Set encoder settings to EEPROM.
	* Can be used by manufacturer only.
	* @param id an identifier of device
	* @param[in] encoder_settings structure contains encoder settings
	* \endenglish
	* \russian
	* Запись настроек энкодера в EEPROM.
	* Функция должна использоваться только производителем.
	* @param id идентификатор устройства
	* @param[in] encoder_settings структура, содержащая настройки энкодера
	* \endrussian
	*/
	result_t XIMC_API set_encoder_settings (device_t id, const encoder_settings_t* encoder_settings);

/** 
	* \english
	* Read encoder settings from EEPROM.
	* @param id an identifier of device
	* @param[out] encoder_settings structure contains encoder settings
	* \endenglish
	* \russian
	* Чтение настроек энкодера из EEPROM.
	* @param id идентификатор устройства
	* @param[out] encoder_settings структура, содержащая настройки энкодера
	* \endrussian
	*/
	result_t XIMC_API get_encoder_settings (device_t id, encoder_settings_t* encoder_settings);

/** 
	* \english
	* Set hall sensor information to EEPROM.
	* Can be used by manufacturer only.
	* @param id an identifier of device
	* @param[in] hallsensor_information structure contains information about hall sensor
	* \endenglish
	* \russian
	* Запись информации о датчиках Холла в EEPROM.
	* Функция должна использоваться только производителем.
	* @param id идентификатор устройства
	* @param[in] hallsensor_information структура, содержащая информацию о датчиках Холла
	* \endrussian
	*/
	result_t XIMC_API set_hallsensor_information (device_t id, const hallsensor_information_t* hallsensor_information);

/** 
	* \english
	* Read hall sensor information from EEPROM.
	* @param id an identifier of device
	* @param[out] hallsensor_information structure contains information about hall sensor
	* \endenglish
	* \russian
	* Чтение информации о датчиках Холла из EEPROM.
	* @param id идентификатор устройства
	* @param[out] hallsensor_information структура, содержащая информацию о датчиках Холла
	* \endrussian
	*/
	result_t XIMC_API get_hallsensor_information (device_t id, hallsensor_information_t* hallsensor_information);

/** 
	* \english
	* Set hall sensor settings to EEPROM.
	* Can be used by manufacturer only.
	* @param id an identifier of device
	* @param[in] hallsensor_settings structure contains hall sensor settings
	* \endenglish
	* \russian
	* Запись настроек датчиков Холла в EEPROM.
	* Функция должна использоваться только производителем.
	* @param id идентификатор устройства
	* @param[in] hallsensor_settings структура, содержащая настройки датчиков Холла
	* \endrussian
	*/
	result_t XIMC_API set_hallsensor_settings (device_t id, const hallsensor_settings_t* hallsensor_settings);

/** 
	* \english
	* Read hall sensor settings from EEPROM.
	* @param id an identifier of device
	* @param[out] hallsensor_settings structure contains hall sensor settings
	* \endenglish
	* \russian
	* Чтение настроек датчиков Холла из EEPROM.
	* @param id идентификатор устройства
	* @param[out] hallsensor_settings структура, содержащая настройки датчиков Холла
	* \endrussian
	*/
	result_t XIMC_API get_hallsensor_settings (device_t id, hallsensor_settings_t* hallsensor_settings);

/** 
	* \english
	* Set gear information to EEPROM.
	* Can be used by manufacturer only.
	* @param id an identifier of device
	* @param[in] gear_information structure contains information about step gearhead
	* \endenglish
	* \russian
	* Запись информации о редукторе в EEPROM.
	* Функция должна использоваться только производителем.
	* @param id идентификатор устройства
	* @param[in] gear_information структура, содержащая информацию о редукторе
	* \endrussian
	*/
	result_t XIMC_API set_gear_information (device_t id, const gear_information_t* gear_information);

/** 
	* \english
	* Read gear information from EEPROM.
	* @param id an identifier of device
	* @param[out] gear_information structure contains information about step gearhead
	* \endenglish
	* \russian
	* Чтение информации о редукторе из EEPROM.
	* @param id идентификатор устройства
	* @param[out] gear_information структура, содержащая информацию о редукторе
	* \endrussian
	*/
	result_t XIMC_API get_gear_information (device_t id, gear_information_t* gear_information);

/** 
	* \english
	* Set gear settings to EEPROM.
	* Can be used by manufacturer only.
	* @param id an identifier of device
	* @param[in] gear_settings structure contains step gearhead settings
	* \endenglish
	* \russian
	* Запись настроек редуктора в EEPROM.
	* Функция должна использоваться только производителем.
	* @param id идентификатор устройства
	* @param[in] gear_settings структура, содержащая настройки редуктора
	* \endrussian
	*/
	result_t XIMC_API set_gear_settings (device_t id, const gear_settings_t* gear_settings);

/** 
	* \english
	* Read gear settings from EEPROM.
	* @param id an identifier of device
	* @param[out] gear_settings structure contains step gearhead settings
	* \endenglish
	* \russian
	* Чтение настроек редуктора из EEPROM.
	* @param id идентификатор устройства
	* @param[out] gear_settings структура, содержащая настройки редуктора
	* \endrussian
	*/
	result_t XIMC_API get_gear_settings (device_t id, gear_settings_t* gear_settings);

/** 
	* \english
	* Set additional accessories information to EEPROM.
	* Can be used by manufacturer only.
	* @param id an identifier of device
	* @param[in] accessories_settings structure contains information about additional accessories
	* \endenglish
	* \russian
	* Запись информации о дополнительных аксессуарах в EEPROM.
	* Функция должна использоваться только производителем.
	* @param id идентификатор устройства
	* @param[in] accessories_settings структура, содержащая информацию о дополнительных аксессуарах
	* \endrussian
	*/
	result_t XIMC_API set_accessories_settings (device_t id, const accessories_settings_t* accessories_settings);

/** 
	* \english
	* Read additional accessories information from EEPROM.
	* @param id an identifier of device
	* @param[out] accessories_settings structure contains information about additional accessories
	* \endenglish
	* \russian
	* Чтение информации о дополнительных аксессуарах из EEPROM.
	* @param id идентификатор устройства
	* @param[out] accessories_settings структура, содержащая информацию о дополнительных аксессуарах
	* \endrussian
	*/
	result_t XIMC_API get_accessories_settings (device_t id, accessories_settings_t* accessories_settings);

/** 
	* \english
	* Read controller's firmware version.
	* @param id an identifier of device
	* @param[out] Major major version
	* @param[out] Minor minor version
	* @param[out] Release release version
	* \endenglish
	* \russian
	* Чтение номера версии прошивки контроллера.
	* @param id идентификатор устройства
	* @param[out] Major номер основной версии
	* @param[out] Minor номер дополнительной версии
	* @param[out] Release номер релиза
	* \endrussian
	*/
	result_t XIMC_API get_bootloader_version (device_t id, unsigned int* Major, unsigned int* Minor, unsigned int* Release);

/** 
	* \english
	* Read random number from controller.
	* @param id an identifier of device
	* @param[out] init_random random sequence generated by the controller
	* \endenglish
	* \russian
	* Чтение случайного числа из контроллера.
	* @param id идентификатор устройства
	* @param[out] init_random случайная последовательность, сгенерированная контроллером
	* \endrussian
	*/
	result_t XIMC_API get_init_random (device_t id, init_random_t* init_random);

/** 
  * \english
  * This value is unique to each individual die but is not a random value.
  * This unique device identifier can be used to initiate secure boot processes
  * or as a serial number for USB or other end applications.
  * @param id an identifier of device
  * @param[out] globally_unique_identifier the result of fields 0-3 concatenated defines the unique 128-bit device identifier.
  * \endenglish
  * \russian
  * Считывает уникальный идентификатор каждого чипа, это значение не является случайным.
  * Уникальный идентификатор может быть использован в качестве инициализационного вектора
  * для операций шифрования бутлоадера или в качестве серийного номера для USB и других применений.
  * @param id идентификатор устройства
  * @param[out] globally_unique_identifier результат полей 0-3 определяет уникальный 128-битный идентификатор.
  * \endrussian
  */
	result_t XIMC_API get_globally_unique_identifier (device_t id, globally_unique_identifier_t* globally_unique_identifier);


/*
 -------------------------
   END OF GENERATED CODE
 -------------------------
*/

/* hand-crafted functions begin */

	/**
		* \english
		* Reboot to firmware
		* @param id an identifier of device
		* @param[out] ret RESULT_OK, if reboot to firmware is possible. Reboot is done after reply to this command. RESULT_NO_FIRMWARE, if firmware is not found. RESULT_ALREADY_IN_FIRMWARE, if this command was sent when controller is already in firmware.
		* \endenglish
		* \russian
		* Перезагрузка в прошивку в контроллере
		* @param id идентификатор устройства
		* @param[out] ret RESULT_OK, если переход из загрузчика в прошивку возможен. После ответа на эту команду выполняется переход. RESULT_NO_FIRMWARE, если прошивка не найдена. RESULT_ALREADY_IN_FIRMWARE, если эта команда была вызвана из прошивки.
		* \endrussian
		*/
	result_t XIMC_API goto_firmware(device_t id, uint8_t* ret);

	/**
		* \english
		* Check for firmware on device
		* @param uri a uri of device
		* @param[out] ret non-zero if firmware existed
		* \endenglish
		* \russian
		* Проверка наличия прошивки в контроллере
		* @param uri уникальный идентификатор ресурса устройства
		* @param[out] ret ноль, если прошивка присутствует
		* \endrussian
		*/
	result_t XIMC_API has_firmware(const char* uri, uint8_t* ret);

	/**
		* \english
		* Update firmware.
		* Service command
		* @param uri a uri of device
		* @param data firmware byte stream
		* @param data_size size of byte stream
		* \endenglish
		* \russian
		* Обновление прошивки
		* @param uri идентификатор устройства
		* @param data указатель на массив байтов прошивки
		* @param data_size размер массива в байтах
		* \endrussian
		*/
	result_t XIMC_API command_update_firmware(const char* uri, const uint8_t* data, uint32_t data_size);

/**
	* \english
	* Write controller key.
	* Can be used by manufacturer only
	* @param uri a uri of device
	* @param[in] key protection key. Range: 0..4294967295
	* \endenglish
	* \russian
	* Запись ключа защиты
	* Функция используется только производителем.
	* @param uri идентификатор устройства
	* @param[in] key ключ защиты. Диапазон: 0..4294967295
	* \endrussian
	*/
	result_t XIMC_API write_key (const char* uri, uint8_t* key);

/**
	* \english
	* Reset controller.
	* Can be used by manufacturer only
	* @param id an identifier of device
	* \endenglish
	* \russian
	* Перезагрузка контроллера.
	* Функция используется только производителем.
	* @param id идентификатор устройства
	* \endrussian
	*/
	result_t XIMC_API command_reset(device_t id);

/**
	* \english
	* Clear controller FRAM.
	* Can be used by manufacturer only
	* @param id an identifier of device
	* \endenglish
	* \russian
	* Очистка FRAM памяти контроллера.
	* Функция используется только производителем.
	* @param id идентификатор устройства
	* \endrussian
	*/
	result_t XIMC_API command_clear_fram(device_t id);

	//@}

	// ------------------------------------

	/**
		\english
		@name Boards and drivers control
		* Functions for searching and opening/closing devices
		\endenglish
		\russian
		@name Управление устройством
		* Функции поиска и открытия/закрытия устройств
		\endrussian
		*/
	//@{

	/**
		* \english
		* Open a device with OS uri \a uri and return identifier of the device which can be used in calls.
		* @param[in] uri - a device uri.
		* Device uri has form "xi-com:port" or "xi-net://host/serial" or "xi-emu:///file".
		* In case of USB-COM port the "port" is the OS device uri.
		* For example "xi-com:\\\.\COM3" in Windows or "xi-com:/dev/tty.s123" in Linux/Mac.
		* In case of network device the "host" is an IPv4 address or fully qualified domain uri (FQDN), "serial" is the device serial number in hexadecimal system.
		* For example "xi-net://192.168.0.1/00001234" or "xi-net://hostname.com/89ABCDEF".
		* Note: to open network device you must call {@link set_bindy_key} first.
		* In case of virtual device the "file" is the full filename with device memory state, if it doesn't exist then it is initialized with default values.
		* For example "xi-emu:///C:/dir/file.bin" in Windows or "xi-emu:///home/user/file.bin" in Linux/Mac.
		* \endenglish
		* \russian
		* Открывает устройство по имени \a uri и возвращает идентификатор, который будет использоваться для обращения к устройству.
		* @param[in] uri - уникальный идентификатор устройства.
		* Uri устройства имеет вид "xi-com:port" или "xi-net://host/serial" или "xi-emu:///file".
		* Для USB-COM устройства "port" это uri устройства в ОС.
		* Например "xi-com:\\\.\COM3" в Windows или "xi-com:/dev/tty.s123" в Linux/Mac.
		* Для сетевого устройства "host" это IPv4 адрес или полностью определённое имя домена, "serial" это серийный номер устройства в шестнадцатеричной системе.
		* Например "xi-net://192.168.0.1/00001234" или "xi-net://hostname.com/89ABCDEF".
		* Замечание: для открытия сетевого устройства обязательно нужно сначала вызвать функцию установки сетевого ключа {@link set_bindy_key}.
		* Для виртуального устройства "file" это путь к файлу с сохраненным состоянием устройства. Если файл не существует, он будет создан и инициализирован значениями по умолчанию.
		* Например "xi-emu:///C:/dir/file.bin" в Windows или "xi-emu:///home/user/file.bin" в Linux/Mac.
		* \endrussian
		*/
	device_t XIMC_API open_device (const char* uri);

	/**
		* \english
		* Close specified device
		* @param id an identifier of device
		* \note
		* The id parameter in this function is a C pointer, unlike most library functions that use this parameter
		* \endenglish
		* \russian
		* Закрывает устройство
		* @param id - идентификатор устройства
		* \note
		* Параметр id в данной функции является Си указателем, в отличие от большинства функций библиотеки использующих данный параметр
		* \endrussian
		*/
	result_t XIMC_API close_device (device_t* id);

	/**
		* \english
		* Command of loading a correction table from a text file (this function is deprecated).
		* Use the function set_correction_table(device_t id, const char* namefile).
		* The correction table is used for position correction in case of mechanical inaccuracies.
		* It works for some parameters in _calb commands.
		* @param id an identifier the device
		* @param[in] namefile - the file name must be fully qualified.
		* If the short name is used, the file must be located in the application directory.
		* If the file name is set to NULL, the correction table will be cleared.
		* File format: two tab-separated columns.
		* Column headers are string.
		* Data is real, the point is a determiter.
		* The first column is a coordinate. The second one is the deviation caused by a mechanical error.
		* The maximum length of a table is 100 rows.
		* \note
		* The id parameter in this function is a C pointer, unlike most library functions that use this parameter
		* @see command_move
		* @see get_position_calb
		* @see get_position_calb_t
		* @see get_status_calb
		* @see status_calb_t
		* @see get_edges_settings_calb
		* @see set_edges_settings_calb
		* @see edges_settings_calb_t
		*
		* \endenglish
		* \russian
		* Команда загрузки корректирующей таблицы из текстового файла (данная функция устарела).
		* Используйте функцию set_correction_table(device_t id, const char* namefile).
		* Таблица используется для коррекции положения в случае механических неточностей.
		* Работает для некоторых параметров в _calb командах.
		* @param id - идентификатор устройства
		* @param[in] namefile - имя файла должно быть полным.
		* Если используется короткое имя, файл должен находится в директории приложения.
		* Если имя файла равно NULL таблица коррекции будет очищена.
		* Формат файла: два столбца разделенных табуляцией.
		* Заголовки столбцов строковые.
		* Данные действительные разделитель точка.
		* Первый столбец координата. Второй - отклонение вызванное ошибкой механики.
		* Между координатами отклонение расчитывается линейно. За диапазоном константа равная отклонению на границе.
		* Максимальная длина таблицы 100 строк.		
		* \note
		* Параметр id в данной функции является Си указателем, в отличие от большинства функций библиотеки использующих данный параметр
		* @see command_move
		* @see command_movr
		* @see get_position_calb
		* @see get_position_calb_t
		* @see get_status_calb
		* @see status_calb_t
		* @see get_edges_settings_calb
		* @see set_edges_settings_calb
		* @see edges_settings_calb_t
		* \endrussian
		*/
	result_t XIMC_API load_correction_table(device_t* id, const char* namefile);

	/**
	* \english
	* Command of loading a correction table from a text file.
	* The correction table is used for position correction in case of mechanical inaccuracies.
	* It works for some parameters in _calb commands.
	* @param id an identifier the device
	* @param[in] namefile - the file name must be fully qualified.
	* If the short name is used, the file must be located in the application directory.
	* If the file name is set to NULL, the correction table will be cleared.
	* File format: two tab-separated columns.
	* Column headers are string.
	* Data is real, the point is a determiter.
	* The first column is a coordinate. The second one is the deviation caused by a mechanical error.
	* The maximum length of a table is 100 rows.
	* @see command_move
	* @see get_position_calb
	* @see get_position_calb_t
	* @see get_status_calb
	* @see status_calb_t
	* @see get_edges_settings_calb
	* @see set_edges_settings_calb
	* @see edges_settings_calb_t
	*
	* \endenglish
	* \russian
	* Команда загрузки корректирующей таблицы из текстового файла.
	* Таблица используется для коррекции положения в случае механических неточностей.
	* Работает для некоторых параметров в _calb командах.
	* @param id - идентификатор устройства
	* @param[in] namefile - имя файла должно быть полным.
	* Если используется короткое имя, файл должен находится в директории приложения.
	* Если имя файла равно NULL таблица коррекции будет очищена.
	* Формат файла: два столбца разделенных табуляцией.
	* Заголовки столбцов строковые.
	* Данные действительные разделитель точка.
	* Первый столбец координата. Второй - отклонение вызванное ошибкой механики.
	* Между координатами отклонение расчитывается линейно. За диапазоном константа равная отклонению на границе.
	* Максимальная длина таблицы 100 строк.
	* @see command_move
	* @see command_movr
	* @see get_position_calb
	* @see get_position_calb_t
	* @see get_status_calb
	* @see status_calb_t
	* @see get_edges_settings_calb
	* @see set_edges_settings_calb
	* @see edges_settings_calb_t
	* \endrussian
	*/
	result_t XIMC_API set_correction_table(device_t id, const char* namefile);

	/**
		* \english
		* Check if a device with OS uri \a uri is XIMC device.
		* Be carefuly with this call because it sends some data to the device.
		* @param[in] uri - a device uri
		* \endenglish
		* \russian
		* Проверяет, является ли устройство с уникальным идентификатором \a uri XIMC-совместимым.
		* Будьте осторожны с вызовом этой функции для неизвестных устройств, т.к. она отправляет данные.
		* @param[in] uri - уникальный идентификатор устройства
		* \endrussian
		*/
	result_t XIMC_API probe_device (const char* uri);

	/**
		* \english
		* Set network encryption layer (bindy) key.
		* @param[in] keyfilepath full path to the bindy keyfile
		* When using network-attached devices this function must be called before {@link enumerate_devices} and {@link open_device} functions.
		* \endenglish
		* \russian
		* Устанавливливает ключ шифрования сетевой подсистемы (bindy).
		* @param[in] keyfilepath полный путь к файлу ключа
		* В случае использования сетевых устройств эта функция должна быть вызвана до функций {@link enumerate_devices} и {@link open_device}.
		* \endrussian
	 */
	result_t XIMC_API set_bindy_key(const char* keyfilepath);

	/**
		* \english
		* Enumerate all devices that looks like valid.
		* @param[in] enumerate_flags enumerate devices flags
		* @param[in] hints extended information
		* hints is a string of form "key=value \n key2=value2". Unrecognized key-value pairs are ignored.
		* Key list: addr - used together with ENUMERATE_NETWORK flag.
		* Non-null value is a remote host name or a comma-separated list of host names which contain the devices to be found, absent value means broadcast discovery.
		* adapter_addr - used together with ENUMERATE_NETWORK flag.
		* Non-null value is a IP address of network adapter. Remote ximc device must be on the same local network as the adapter.
		* When using the adapter_addr key, you must install the addr key. Example: "addr= \n adapter_addr=192.168.0.100".
		* To enumerate network devices you must call {@link set_bindy_key} first.
		* \endenglish
		* \russian
		* Перечисляет все XIMC-совместимые устройства.
		* @param[in] enumerate_flags флаги поиска устройств
		* @param[in] hints дополнительная информация для поиска
		* hints это строка вида "ключ1=значение1 \n ключ2=значение2". Неизвестные пары ключ-значение игнорируются.
		* Список ключей: addr - используется вместе с флагом ENUMERATE_NETWORK.
		* Ненулевое значение это адрес или список адресов с перечислением через запятую удаленных хостов на которых происходит поиск устройств, отсутствующее значение это подключение посредством широковещательного запроса.
		* adapter_addr - используется вместе с флагом ENUMERATE_NETWORK.
		* Ненулевое значение это IP адрес сетевого адаптера. Сетевое устройство ximc должно быть в локальной сети, к которой подключён этот адаптер.
		* При использование ключа adapter_addr обязательно установить ключ addr. Пример: "addr= \n adapter_addr=192.168.0.100".
		* Для перечисления сетевых устройств обязательно нужно сначала вызвать функцию установки сетевого ключа {@link set_bindy_key}.
		* \endrussian
	 */
	device_enumeration_t XIMC_API enumerate_devices(int enumerate_flags, const char *hints);

	/**
		* \english
		* Free memory returned by \a enumerate_devices.
		* @param[in] device_enumeration opaque pointer to an enumeration device data
		* \endenglish
		* \russian
		* Освобождает память, выделенную \a enumerate_devices.
		* @param[in] device_enumeration закрытый указатель на данные о перечисленных устойствах
		* \endrussian
	 */
	result_t XIMC_API free_enumerate_devices(device_enumeration_t device_enumeration);

	/**
		* \english
		* Get device count.
		* @param[in] device_enumeration opaque pointer to an enumeration device data
		* \endenglish
		* \russian
		* Возвращает количество подключенных устройств.
		* @param[in] device_enumeration закрытый указатель на данные о перечисленных устойствах
		* \endrussian
	 */
	int XIMC_API get_device_count(device_enumeration_t device_enumeration);

	/**
		* \english
		* Nevermind
		* \endenglish
		* \russian
		* Не обращайте на меня внимание
		* \endrussian
	*/
	typedef char* pchar;

	/**
		* \english
		* Get device name from the device enumeration.
		* Returns \a device_index device name.
		* @param[in] device_enumeration opaque pointer to an enumeration device data
		* @param[in] device_index device index
		* \endenglish
		* \russian
		* Возвращает имя подключенного устройства из перечисления устройств.
		* Возвращает имя устройства с номером \a device_index.
		* @param[in] device_enumeration закрытый указатель на данные о перечисленных устойствах
		* @param[in] device_index номер устройства
		* \endrussian
	 */
	pchar XIMC_API get_device_name(device_enumeration_t device_enumeration, int device_index);


	/**
		* \english
		* Get device serial number from the device enumeration.
		* Returns \a device_index device serial number.
		* @param[in] device_enumeration opaque pointer to an enumeration device data
		* @param[in] device_index device index
		* @param[out] serial device serial number
		* \endenglish
		* \russian
		* Возвращает серийный номер подключенного устройства из перечисления устройств.
		* Возвращает серийный номер устройства с номером \a device_index.
		* @param[in] device_enumeration закрытый указатель на данные о перечисленных устойствах
		* @param[in] device_index номер устройства
		* @param[in] serial серийный номер устройства
		* \endrussian
	 */
	result_t XIMC_API get_enumerate_device_serial(device_enumeration_t device_enumeration, int device_index, uint32_t* serial);

	/**
		* \english
		* Get device information from the device enumeration.
		* Returns \a device_index device information.
		* @param[in] device_enumeration opaque pointer to an enumeration device data
		* @param[in] device_index device index
		* @param[out] device_information device information data
		* \endenglish
		* \russian
		* Возвращает информацию о подключенном устройстве из перечисления устройств.
		* Возвращает информацию о устройстве с номером \a device_index.
		* @param[in] device_enumeration закрытый указатель на данные о перечисленных устойствах
		* @param[in] device_index номер устройства
		* @param[out] device_information информация об устройстве
		* \endrussian
	 */
	result_t XIMC_API get_enumerate_device_information(device_enumeration_t device_enumeration, int device_index, device_information_t* device_information);

	/**
		* \english
		* Get controller name from the device enumeration.
		* Returns \a device_index device controller name.
		* @param[in] device_enumeration opaque pointer to an enumeration device data
		* @param[in] device_index device index
		* @param[out] controller_name controller name
		* \endenglish
		* \russian
		* Возвращает имя подключенного устройства из перечисления устройств.
		* Возвращает имя устройства с номером \a device_index.
		* @param[in] device_enumeration закрытый указатель на данные о перечисленных устойствах
		* @param[in] device_index номер устройства
		* @param[out] controller name имя устройства
		* \endrussian
	 */
	result_t XIMC_API get_enumerate_device_controller_name(device_enumeration_t device_enumeration, int device_index, controller_name_t* controller_name);

	/**
		* \english
		* Get stage name from the device enumeration.
		* Returns \a device_index device stage name.
		* @param[in] device_enumeration opaque pointer to an enumeration device data
		* @param[in] device_index device index
		* @param[out] stage_name stage name
		* \endenglish
		* \russian
		* Возвращает имя подвижки для подключенного устройства из перечисления устройств.
		* Возвращает имя подвижки устройства с номером \a device_index.
		* @param[in] device_enumeration закрытый указатель на данные о перечисленных устойствах
		* @param[in] device_index номер устройства
		* @param[out] stage name имя подвижки
		* \endrussian
	 */
	result_t XIMC_API get_enumerate_device_stage_name(device_enumeration_t device_enumeration, int device_index, stage_name_t* stage_name);

	/**
		* \english
		* Get device network information from the device enumeration.
		* Returns \a device_index device network information.
		* @param[in] device_enumeration opaque pointer to an enumeration device data
		* @param[in] device_index device index
		* @param[out] device_network_information device network information data
		* \endenglish
		* \russian
		* Возвращает сетевую информацию о подключенном устройстве из перечисления устройств.
		* Возвращает сетевую информацию о устройстве с номером \a device_index.
		* @param[in] device_enumeration закрытый указатель на данные о перечисленных устойствах
		* @param[in] device_index номер устройства
		* @param[out] device_network_information сетевая информация об устройстве
		* \endrussian
	 */
	result_t XIMC_API get_enumerate_device_network_information(device_enumeration_t device_enumeration, int device_index, device_network_information_t* device_network_information);

	/** \english
		* Resets the error of incorrect data transmission. This function returns only 0 (OK). 
		* For example, sending the libximc command ends with an incorrect data transfer (error), any subsequent command always returns -1 (relevant for Windows).
		* \endenglish
		* \russian
		* Сбрасывает ошибку неправильной передачи данных. Эта функция возвращает только 0 (OK). 
		* Например, отправка команды libximc заканчивается неправильной передачей данных (ошибкой), любая последующая команда всегда возвращает -1 (актуально для Windows).
		* \endrussian
	*/
	result_t XIMC_API reset_locks ();

	/** \english
		* Fixing a USB driver error in Windows.
		* The USB-COM subsystem in the Windows OS does not always work correctly. During operation, the following malfunctions are possible:
		* All attempts to open the device fail. The device can be opened and data can be sent to it, but the response data is not received.
		* These problems are fixed by reconnecting the device or reinitializing it in the Device Manager.
		* The ximc_fix_usbser_sys() function automates the deletion detection process.
		* \endenglish
		* \russian
		* Исправление ошибки драйвера USB в Windows.
		* Подсистема USB-COM на OC Windows не всегда работает корректно. При работе возможны следующие неисправности:
		* Все попытки открыть устройство заканчиваются неудачно. Устройство можно открыть и отправить в него данные, но ответные данные не приходят.
		* Эти проблемы исправляются переподключением устройства или его переинециализацией в диспетчере устройств.
		* Функция ximc_fix_usbser_sys() автоматизирует процесс удаления-обнаружения.
		* \endrussian
		*/
	result_t XIMC_API ximc_fix_usbser_sys(const char* device_uri);


	/** \english
		* Sleeps for a specified amount of time
		* @param msec time in milliseconds
		* \endenglish
		* \russian
		* Приостанавливает работу на указанное время
		* @param msec время в миллисекундах
		* \endrussian
		*/
	void XIMC_API msec_sleep (unsigned int msec);

	/** \english
		* Returns a library version
		* @param version a buffer to hold a version string, 32 bytes is enough
		* \endenglish
		* \russian
		* Возвращает версию библиотеки
		* @param version буфер для строки с версией, 32 байт достаточно
		* \endrussian
		*/
	void XIMC_API ximc_version (char* version);

#if !defined(MATLAB_IMPORT) && !defined(LABVIEW64_IMPORT) && !defined(LABVIEW32_IMPORT)

	/** \english
		* Logging callback prototype
		* @param loglevel a loglevel
		* @param message a message
		* \endenglish
		* \russian
		* Прототип функции обратного вызова для логирования
		* @param loglevel уровень логирования
		* @param message сообщение
		* \endrussian
		*/
	typedef void (XIMC_CALLCONV *logging_callback_t)(int loglevel, const wchar_t* message, void* user_data);

	/** \english
		* Simple callback for logging to stderr in wide chars
		* @param loglevel a loglevel
		* @param message a message
		* \endenglish
		* \russian
		* Простая функция логирования на stderr в широких символах
		* @param loglevel уровень логирования
		* @param message сообщение
		* \endrussian
		*/
	void XIMC_API logging_callback_stderr_wide(int loglevel, const wchar_t* message, void* user_data);

	/** \english
		* Simple callback for logging to stderr in narrow (single byte) chars
		* @param loglevel a loglevel
		* @param message a message
		* \endenglish
		* \russian
		* Простая функция логирования на stderr в узких (однобайтных) символах
		* @param loglevel уровень логирования
		* @param message сообщение
		* \endrussian
		*/
	void XIMC_API logging_callback_stderr_narrow(int loglevel, const wchar_t* message, void* user_data);

	/**
		* \english
		* Sets a logging callback.
		* Call resets a callback to default (stderr, syslog) if NULL passed.
		* @param logging_callback a callback for log messages
		* \endenglish
		* \russian
		* Устанавливает функцию обратного вызова для логирования.
		* Вызов назначает стандартный логгер (stderr, syslog), если передан NULL
		* @param logging_callback указатель на функцию обратного вызова
		* \endrussian
		*/
	void XIMC_API set_logging_callback(logging_callback_t logging_callback, void* user_data);

#endif

/**
	* \english
	* Return device state.
	* @param id an identifier of device
	* @param[out] status structure with snapshot of controller status
	* \endenglish
	* \russian
	* Возвращает информацию о текущем состоянии устройства.
	* @param id идентификатор устройства
	* @param[out] status структура с информацией о текущем состоянии устройства
	* \endrussian
	*/
/**
	* \english
	* Device state.
	* Useful structure that contains current controller status, including speed, position and boolean flags.
	* \endenglish
	* \russian
	* Состояние устройства.
	* Эта структура содержит основные параметры текущего состояния контроллера, такие как скорость, позиция и флаги состояния.
	* \endrussian
	* @see get_status
	*/
	result_t XIMC_API get_status (device_t id, status_t* status);

/**
	* \english
	* Return device state.
	* @param id an identifier of device
	* @param[out] status structure with snapshot of controller status
	* @param calibration user unit settings
	* \endenglish
	* \russian
	* Возвращает информацию о текущем состоянии устройства.
	* @param id идентификатор устройства
	* @param[out] status структура с информацией о текущем состоянии устройства
	* @param calibration настройки пользовательских единиц
	* \endrussian
	*/
/**
	* \english
	* Calibrated device state.
	* Useful structure that contains current controller status, including speed, position and boolean flags.
	* \endenglish
	* \russian
	* Состояние устройства в калиброванных единицах.
	* Эта структура содержит основные параметры текущего состояния контроллера, такие как скорость, позиция и флаги состояния, размерные величины выводятся в калиброванных единицах.
	* \endrussian
	* @see get_status
	*/
	result_t XIMC_API get_status_calb (device_t id, status_calb_t* status, const calibration_t* calibration);

/**
	* \english
	* Return device information.
	* All fields must point to allocated string buffers with at least 10 bytes.
	* Works with both raw or initialized device.
	* @param id an identifier of device
	* @param[out] device_information device information
	* \endenglish
	* \russian
	* Возвращает информацию об устройстве.
	* Все входные параметры должны быть указателями на выделенные области памяти длиной не менее 10 байт.
	* Команда доступна как из инициализированного состояния, так и из исходного.
	* @param id идентификатор устройства.
	* @param[out] device_information информация об устройстве
	* \endrussian
	*/
/**
	* \english
	* Device information.
	* \endenglish
	* \russian
	* Информация об устройстве.
	* \endrussian
	* @see get_device_information
	*/
	result_t XIMC_API get_device_information (device_t id, device_information_t* device_information);

/**
	* \english
	* Wait for stop
	* @param id an identifier of device
	* @param refresh_interval_ms Status refresh interval. The function waits this number of milliseconds between get_status requests to the controller.
	* Recommended value of this parameter is 10 ms. Use values of less than 3 ms only when necessary - small refresh interval values do not significantly
	* increase response time of the function, but they create substantially more traffic in controller-computer data channel.
	* @param[out] ret RESULT_OK if controller has stopped and result of the first get_status command which returned anything other than RESULT_OK otherwise.
	* \endenglish
	* \russian
	* Ожидание остановки контроллера
	* @param id идентификатор устройства
	* @param refresh_interval_ms Интервал обновления. Функция ждет столько миллисекунд между отправками контроллеру запроса get_status для проверки статуса остановки.
	* Рекомендуемое значение интервала обновления - 10 мс. Используйте значения меньше 3 мс только если это необходимо - малые значения интервала обновления
	* незначительно ускоряют обнаружение остановки, но создают существенно больший поток данных в канале связи контроллер-компьютер.
	* @param[out] ret RESULT_OK, если контроллер остановился, в противном случае первый результат выполнения команды get_status со статусом отличным от RESULT_OK.
	* \endrussian
	*/
	result_t XIMC_API command_wait_for_stop(device_t id, uint32_t refresh_interval_ms);
	
	/**
	* \english
	* Make home command, wait until it is finished and make zero command. This is a convinient way to calibrate zero position.
	* @param id an identifier of device
	* @param[out] ret RESULT_OK if controller has finished home & zero correctly or result of first controller query that returned anything other than RESULT_OK.
	* \endenglish
	* \russian
	* Запустить процедуру поиска домашней позиции, подождать её завершения и обнулить позицию в конце. Это удобный путь для калибровки нулевой позиции.
	* @param id идентификатор устройства
	* @param[out] ret RESULT_OK, если контроллер завершил выполнение home и zero корректно или результат первого запроса к контроллеру со статусом отличным от RESULT_OK.
	* \endrussian
	*/
	result_t XIMC_API command_homezero(device_t id);
	//@}

#if defined(__cplusplus)
};
#endif

#endif

// vim: ts=4 shiftwidth=4

