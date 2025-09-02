# -*- coding: utf-8 -*-
import importlib
import os

root_path = os.getcwd()
pos = root_path.find("AKautotest")
if pos == -1:
    print("runtime error")
    exit(1)
root_path = root_path[0:pos + len("AKautotest")]

from akcommon_define import *
from unittest.case import _Outcome, _addSkip
import sys
import time
import datetime as dt
import unittest
from functools import wraps
import traceback
import inspect
import ddt
import pkgutil
import warnings


def unittest_assert_results() -> bool:
    """
    检查结果是否存在失败
    Returns: 如果存在断言失败，返回False，反之返回True
    """
    results = param_get_test_results()
    if not results:
        return True
    for result in results:
        if not isinstance(result, list):
            continue
        if _assert_fail(result[0]):
            return False
    return True


def unittest_check_results_screenshot(*devices_instance):
    """检查结果是否存在失败，并截图"""
    if not devices_instance:
        return
    results = param_get_test_results()
    if not results:
        return
    assert_ret = True
    for result in results:
        if not isinstance(result, list):
            continue
        if _assert_fail(result[0]):
            assert_ret = False
            break
    if not assert_ret:
        for device in devices_instance:
            if hasattr(device, 'screen_shot'):
                device.screen_shot()
            elif hasattr(device, 'app') and hasattr(device.app, 'screen_shot'):
                device.app.screen_shot()


def failed_robot(msg, receiverlist=None):
    """压测中失败手动发送失败消息给为企业微信机器人"""

    def test(func):
        @wraps(func)
        def test1(self, *args, **kwargs):
            try:
                ret = func(self, *args, **kwargs)
            except:
                content = func.__name__ + '  -->  ' + msg
                robot_info_msg(content, receiverlist)
                raise
            else:
                try:
                    if self.verificationErrors != []:
                        content = func.__name__ + '  -->  ' + msg
                        robot_info_msg(content, receiverlist)
                except:
                    print(traceback.format_exc())
                    pass
            return ret

        return test1

    return test


def unittest_pcap(*devices_or_names):
    """
    设备抓包装饰器，支持传入设备实例或参数名（字符串）。
    - 设备参数名：自动从被装饰函数参数中获取设备实例
    - 设备实例：直接使用
    用于unittest.TestCase用例类或封装的用例操作步骤函数
    """
    def decorator(test_func):
        @wraps(test_func)
        def wrapper(*args, **kwargs):
            aklog_info(f'devices_or_names: {devices_or_names}')
            # 获取函数签名和参数映射
            try:
                sig = inspect.signature(test_func)
                bound_args = sig.bind(*args, **kwargs)
                bound_args.apply_defaults()
                params = bound_args.arguments  # OrderedDict
            except Exception as e:
                aklog_error(f'参数绑定失败: {e}')
                params = {}

            # 设备实例收集
            device_list = []
            for item in devices_or_names:
                if isinstance(item, str):
                    # 参数名，尝试从params获取
                    dev = params.get(item)
                    if dev is None and len(args) > 0:
                        # 兼容类方法，从self属性获取
                        self_obj = args[0]
                        dev = getattr(self_obj, item, None)
                    if dev is None:
                        aklog_warn(f'未找到设备实例: {item}')
                    device_list.append(dev)
                else:
                    # 直接是设备实例
                    device_list.append(item)

            # 设备方法查找
            def get_device_func(dev, func_name):
                if not dev:
                    return None
                for attr in [dev,
                             getattr(dev, 'web_inf', None),
                             getattr(dev, 'web', None),
                             getattr(dev, 'browser', None)]:
                    if attr and hasattr(attr, func_name):
                        return getattr(attr, func_name)
                return None

            # 启动抓包
            start_funcs = [get_device_func(dev, 'start_pcap') for dev in device_list if dev]
            start_funcs = [f for f in start_funcs if f]
            if start_funcs:
                print(f'{"-" * 40}启动设备抓包{"-" * 40}')
                thread_start_with_join(*start_funcs, interval=1)
                print("-" * 92)
            fails = []
            result = None
            self_obj = None
            try:
                result = test_func(*args, **kwargs)
                # 检查断言结果
                self_obj = args[0] if len(args) > 0 else None
                # 兼容unittest.TestCase的verificationErrors
                if hasattr(self_obj, 'verificationErrors'):
                    fails = [fail for fail in self_obj.verificationErrors if 'warning :' not in str(fail)]
                # 兼容unittest_assert_results
                elif callable(globals().get('unittest_assert_results', None)):
                    if not unittest_assert_results():
                        fails.append(False)
            except unittest.SkipTest as e:
                raise e
            except Exception as e:
                fails.append(e)
                raise
            finally:
                # 停止抓包
                stop_funcs = [get_device_func(dev, 'stop_pcap') for dev in device_list if dev]
                stop_funcs = [f for f in stop_funcs if f]
                if stop_funcs:
                    print(f'{"-" * 40}停止设备抓包{"-" * 40}')
                    thread_start_with_join(*stop_funcs, interval=1)

                # 失败导出抓包
                if fails:
                    # 获取用例名
                    case_name = (getattr(self_obj, '_testMethodName', None)
                                 or getattr(test_func, '__name__', None)
                                 or 'unknown_case')
                    export_funcs = []
                    for dev in device_list:
                        func = get_device_func(dev, 'save_pcap_to_results_dir')
                        if func:
                            export_funcs.append((func, (case_name,)))
                    if export_funcs:
                        print(f'{"-" * 40}导出设备抓包{"-" * 40}')
                        thread_start_with_join(*export_funcs, interval=1)

            return result
        return wrapper
    return decorator


def unittest_skip_if_case_fail(depend=""):
    """
    作为用例函数的装饰器，当参数中的用例函数执行失败时，跳过该用例的执行
    :param depend: 依赖的用例函数名，默认为空
    :return: wrapper_func
    """

    def wrapper_func(test_func):
        if isinstance(depend, str):
            test_func.__unittest_skip_base_case__ = depend
        else:
            test_func.__unittest_skip_base_case__ = depend.__name__
        return test_func

    return wrapper_func


def unittest_fail_if_case_fail(depend=""):
    """
    fail_dependon方法, 对讲终端使用该接口直接fail. 以修正skip算做failed的失败率统计.
    """

    def wrapper_func(test_func):
        if isinstance(depend, str):
            test_func.__unittest_fail_base_case__ = depend
        else:
            test_func.__unittest_fail_base_case__ = depend.__name__
        return test_func

    return wrapper_func


def skip_dependon(depend=""):
    return unittest_skip_if_case_fail(depend)


def fail_dependon(depend=""):
    """
    fail_dependon方法, 对讲终端使用该接口直接fail. 以修正skip算做failed的失败率统计以及因跳过遗漏分析.
    """
    return unittest_fail_if_case_fail(depend)


def unittest_skip_if(condition, reason):
    """
    重写skipIf方法，condition可以直接传入True或False的参数。
    可以传入函数，比如：@unittest_skip_if(parse_condition, '原因')
    也可以传入self.condition，然后用例里面可以对self.condition进行赋值，之后该用例根据最后赋值的结果判断是否跳过
    比如：@unittest_skip_if('self.parse_condition', '原因')
    """

    def wrapper_func(test_func):
        test_func.__ak_unittest_skip__ = condition
        test_func.__ak_unittest_skip_why__ = reason
        return test_func

    return wrapper_func


def unittest_add_exec_instances(*instances):
    """
    给用例添加要执行的对象，之后可以对用例进行过滤，只执行对应机型的用例
    Args:
        *instances (str):
    """

    def wrapper_func(test_func):
        if instances:
            test_func.__unittest_exec_instance_list__ = list(instances)
        return test_func

    return wrapper_func


def unittest_fail_to_exec_on_teardown(func, *func_args, **func_kwargs):
    """
    作为teardown装饰器，当用例执行失败时，执行func函数再执行teardown，注意：每条用例都会进行判断并执行。
    可以用作测试失败时截图，但注意如果用例同时被fail_to_exec装饰，则会先执行fail_to_exec指定的函数，
    再执行fail_to_exec_on_teardown指定的函数，可能会导致截图的页面不是想要的。
    :param func: 要执行的函数或者函数名称，可以通过函数名称直接调用函数
    比如：device_web_reset_and_init or 'self.master_android_indoor_web.set_key_display_home_area'
    :param func_args: 要执行的函数的参数
    :param func_kwargs: 要执行的函数的参数
    :return:
    """

    def wrapper_func(teardown_func):
        @wraps(teardown_func)  # @wraps：避免被装饰函数自身的信息丢失
        def inner_func(self, *args, **kwargs):
            try:
                verificationErrors = []
                if hasattr(self, 'verificationErrors'):
                    verificationErrors = [fail for fail in self.verificationErrors if 'warning :' not in str(fail)]
                # 获取当前测试结果
                result = self._outcome.result
                # 检查当前用例是否有失败或错误
                has_failures_or_errors = False
                if verificationErrors:
                    has_failures_or_errors = True
                elif result:
                    # 检查 failures 和 errors 中是否包含当前用例
                    test_id = self.id()
                    has_failures_or_errors = (any(test_id in str(failure[0]) for failure in result.failures)
                                              or any(test_id in str(error[0]) for error in result.errors))

                if has_failures_or_errors:
                    try:
                        func_name = func.__name__
                    except:
                        func_name = func.__func__.__name__
                    print('\n{} unittest_fail_to_exec_on_teardown: {} {}\n'.format(
                        '-' * 20, func_name, '-' * 20))
                    if isinstance(func, classmethod):
                        func.__func__(self.__class__, *func_args, **func_kwargs)
                    elif inspect.isfunction(func):
                        # 判断函数的第一个参数是否为self，如果不是self，则不是类函数，执行时第一个参数去掉self
                        func_vars = func.__code__.co_varnames
                        if func_vars:
                            first_var = func_vars[0]
                        else:
                            first_var = None
                        if first_var == 'self':
                            func(self, *func_args, **func_kwargs)
                        else:
                            func(*func_args, **func_kwargs)
                    elif isinstance(func, str):
                        if func.startswith('self.') or func.startswith('cls.'):
                            config_get_and_call_nested_attribute(
                                func, self, *func_args, **func_kwargs)
                        else:
                            config_get_and_call_nested_attribute(
                                func, None, *func_args, **func_kwargs)
                        # eval(func)(*func_args, **func_kwargs)
            except:
                print(traceback.format_exc())

            return teardown_func(self, *args, **kwargs)

        return inner_func

    return wrapper_func


def unittest_fail_to_exec(func, *func_args, **func_kwargs):
    """
    作为用例函数的装饰器，当用例执行失败时，在执行tearDown之前，执行func函数，当多个该装饰器装饰同一个用例函数时，按照自下而上的顺序
    可以用作测试失败时截图
    :param func: 要执行的函数或者函数名称，可以通过函数名称直接调用函数
    比如：device_web_reset_and_init or 'self.master_android_indoor_web.set_key_display_home_area'
    :param func_args: 要执行的函数的参数
    :param func_kwargs: 要执行的函数的参数
    :return:
    """

    def wrapper_func(test_func):
        @wraps(test_func)  # @wraps：避免被装饰函数自身的信息丢失
        def inner_func(self, *args, **kwargs):
            try:
                result = test_func(self, *args, **kwargs)
                try:
                    fails = []
                    if hasattr(self, 'verificationErrors'):
                        fails = [fail for fail in self.verificationErrors if 'warning :' not in str(fail)]

                    if len(fails) > 0:
                        try:
                            func_name = func.__name__
                        except:
                            func_name = func.__func__.__name__
                        print('\n{}verificationErrors, unittest_fail_to_exec: {}{}\n'.format(
                            '-' * 20, func_name, '-' * 20))
                        if isinstance(func, classmethod):
                            func.__func__(self.__class__, *func_args, **func_kwargs)
                        elif inspect.isfunction(func):
                            # 判断函数的第一个参数是否为self，如果不是self，则不是类函数，执行时第一个参数去掉self
                            func_vars = func.__code__.co_varnames
                            if func_vars:
                                first_var = func_vars[0]
                            else:
                                first_var = None
                            if first_var == 'self':
                                func(self, *func_args, **func_kwargs)
                            else:
                                func(*func_args, **func_kwargs)
                        elif isinstance(func, str):
                            if func.startswith('self.') or func.startswith('cls.'):
                                config_get_and_call_nested_attribute(
                                    func, self, *func_args, **func_kwargs)
                            else:
                                config_get_and_call_nested_attribute(
                                    func, None, *func_args, **func_kwargs)
                            # eval(func)(*func_args, **func_kwargs)  # 将函数名称直接转成函数运行
                except:
                    print(traceback.format_exc())
            except unittest.SkipTest as e:
                raise e
            except Exception as e:
                try:
                    func_name = func.__name__
                except:
                    func_name = func.__func__.__name__
                print('\n{}Exception, unittest_fail_to_exec: {}{}\n'.format('-' * 20, func_name, '-' * 20))
                if func == param_put_failed_to_exit_enable and func_args == (True,):
                    try:
                        print('')
                        print('')
                        print('~~~~~~~~~~  Error Tips: ~~~~~~~~~~~')
                        print('执行用例: {} 失败!, 置位[failed_to_exit_enable]结束后续测试!'.format(self.module_name))
                        print('')
                        print('')
                    except:
                        pass
                if isinstance(func, classmethod):
                    func.__func__(self.__class__, *func_args, **func_kwargs)
                elif inspect.isfunction(func):
                    # 判断函数的第一个参数是否为self，如果不是self，则不是类函数，执行时第一个参数去掉self
                    func_vars = func.__code__.co_varnames
                    if func_vars:
                        first_var = func_vars[0]
                    else:
                        first_var = None
                    if first_var == 'self':
                        func(self, *func_args, **func_kwargs)
                    else:
                        func(*func_args, **func_kwargs)
                elif isinstance(func, str):
                    if func.startswith('self.') or func.startswith('cls.'):
                        config_get_and_call_nested_attribute(
                            func, self, *func_args, **func_kwargs)
                    else:
                        config_get_and_call_nested_attribute(
                            func, None, *func_args, **func_kwargs)
                    # eval(func)(*func_args, **func_kwargs)  # 将函数名称直接转成函数运行
                raise e
            return result

        return inner_func

    return wrapper_func


def unittest_fail_to_retry(target=None, max_n=1, func_prefix="test", *excludes):
    """
    失败重试已在BeautifulReport里实现了，该装饰器可以不用
    一个装饰器，用于unittest执行测试用例出现失败后，自动重试执行

    # example_1: test_001默认重试1次
    class ClassA(unittest.TestCase):
        @retry
        def test_001(self):
            raise AttributeError

    # example_2: max_n=2,test_001重试2次
    class ClassB(unittest.TestCase):
        @retry(max_n=2)
        def test_001(self):
            raise AttributeError

    # example_3: test_001重试3次; test_002重试3次
    @retry(max_n=3)
    class ClassC(unittest.TestCase):
        def test_001(self):
            raise AttributeError

        def test_002(self):
            raise AttributeError

    # example_4: test_102重试2次, test_001不参与重试机制
    @retry(max_n=2, func_prefix="test_1")
    class ClassD(unittest.TestCase):
        def test_001(self):
            raise AttributeError

        def test_102(self):
            raise AttributeError

    :param target: 被装饰的对象，可以是class, function
    :param max_n: 重试次数，没有包含必须有的第一次执行
    :param func_prefix: 当装饰class时，可以用于标记哪些测试方法会被自动装饰
    :param excludes: 当装饰class时，可以用于标记哪些测试方法不会被自动装饰，排除掉
    :return: wrapped class 或 wrapped function
    """

    def decorator(func_or_cls):
        if inspect.isfunction(func_or_cls):

            @wraps(func_or_cls)
            def wrapper(*args, **kwargs):
                n = 0
                while n <= max_n:
                    try:
                        n += 1
                        func_or_cls(*args, **kwargs)
                        return
                    except Exception:  # 可以修改要捕获的异常类型
                        if n <= max_n:
                            trace = sys.exc_info()
                            traceback_info = str()
                            for trace_line in traceback.format_exception(trace[0], trace[1], trace[2], 3):
                                traceback_info += trace_line
                            print(traceback_info)  # 输出组装的错误信息
                            args[0].tearDown()
                            args[0].setUp()
                        else:
                            raise

            return wrapper
        elif inspect.isclass(func_or_cls):
            for name, func in list(func_or_cls.__dict__.items()):
                if name in excludes:
                    continue
                if inspect.isfunction(func) and name.startswith(func_prefix):
                    setattr(func_or_cls, name, decorator(func))
            return func_or_cls
        else:
            raise AttributeError

    if target:
        return decorator(target)
    else:
        return decorator


class UnittestFailToRetry:
    """
    失败重试已在BeautifulReport里实现了，该装饰器可以不用
    类装饰器, 功能与Retry一样

    # example_1: test_001默认重试1次
    class ClassA(unittest.TestCase):
        @FailToRetry
        def test_001(self):
            raise AttributeError

    # example_2: max_n=2,test_001重试2次
    class ClassB(unittest.TestCase):
        @FailToRetry(max_n=2)
        def test_001(self):
            raise AttributeError

    # example_3: test_001重试3次; test_002重试3次
    @FailToRetry(max_n=3)
    class ClassC(unittest.TestCase):
        def test_001(self):
            raise AttributeError

        def test_002(self):
            raise AttributeError

    # example_4: test_102重试2次, test_001不参与重试机制
    @FailToRetry(max_n=2, func_prefix="test_1")
    class ClassD(unittest.TestCase):
        def test_001(self):
            raise AttributeError

        def test_102(self):
            raise AttributeError
    """

    def __new__(cls, func_or_cls=None, max_n=1, func_prefix="test", *excludes):
        self = object.__new__(cls)
        if func_or_cls:
            self.__init__(func_or_cls, max_n, func_prefix, *excludes)
            return self(func_or_cls)
        else:
            return self

    def __init__(self, func_or_cls=None, max_n=1, func_prefix="test", *excludes):
        self._prefix = func_prefix
        self._max_n = max_n
        self.excludes = excludes

    def __call__(self, func_or_cls=None):
        if inspect.isfunction(func_or_cls):
            @wraps(func_or_cls)
            def wrapper(*args, **kwargs):
                n = 0
                while n <= self._max_n:
                    try:
                        n += 1
                        func_or_cls(*args, **kwargs)
                        return
                    except Exception:  # 可以修改要捕获的异常类型
                        if n <= self._max_n:
                            trace = sys.exc_info()
                            traceback_info = str()
                            for trace_line in traceback.format_exception(trace[0], trace[1], trace[2], 3):
                                traceback_info += trace_line
                            print(traceback_info)  # 输出组装的错误信息
                            args[0].tearDown()
                            args[0].setUp()
                        else:
                            raise

            return wrapper
        elif inspect.isclass(func_or_cls):
            for name, func in list(func_or_cls.__dict__.items()):
                if name in self.excludes:
                    continue
                if inspect.isfunction(func) and name.startswith(self._prefix):
                    setattr(func_or_cls, name, self(func))
            return func_or_cls
        else:
            raise AttributeError


def unittest_sc_error_to_exec(target=None, exec_func=None, *func_args, **func_kwargs):
    """
    当setUpClass执行出错时，可以执行exec_func这个函数，在用例类里面定义这个exec_func函数时，建议使用类方法，用@classmethod装饰器
    注意：该装饰器跟unittest_exec_sc_and_tc_only_once只能使用一个
    """
    cls = None

    def decorator(func_or_cls):
        if inspect.isclass(func_or_cls):
            nonlocal cls  # 使用函数的外层(非全局)变量
            cls = func_or_cls

            for name, func in list(func_or_cls.__dict__.items()):
                if name == 'setUpClass':
                    setattr(func_or_cls, name, decorator(func))
            return func_or_cls
        else:
            @wraps(func_or_cls)
            def wrapper():
                try:
                    if (isinstance(func_or_cls, classmethod) and
                            str(func_or_cls.__func__.__name__) == 'setUpClass'):
                        func_or_cls.__func__(cls)
                    elif (inspect.isfunction(func_or_cls) and
                          str(func_or_cls.__name__) == 'setUpClass'):
                        func_or_cls(cls)
                except Exception as e:
                    try:
                        if exec_func:
                            print('\n{}unittest_sc_error_to_exec: {}{}\n'.format('-' * 20, str(exec_func), '-' * 20))

                        if not exec_func:
                            pass
                        if isinstance(exec_func, classmethod):
                            exec_func.__func__(cls, *func_args, **func_kwargs)
                        elif inspect.isfunction(exec_func):
                            exec_func(*func_args, **func_kwargs)
                        elif isinstance(exec_func, str):
                            if exec_func.startswith('cls.') or exec_func.startswith('self.'):
                                config_get_and_call_nested_attribute(
                                    exec_func, cls, *func_args, **func_kwargs)
                            else:
                                config_get_and_call_nested_attribute(
                                    exec_func, None, *func_args, **func_kwargs)
                            # eval(exec_func)(*func_args, **func_kwargs)  # 将函数名称直接转成函数运行
                    except:
                        print(traceback.format_exc())

                    raise e

            return wrapper

    if target:
        return decorator(target)
    else:
        return decorator


def unittest_exec_sc_and_tc_only_once(target=None, exec_func=None, *func_args, **func_kwargs):
    """
    重复执行一个用例模块时，只在第一遍执行setUpClass和最后一遍执行tearDownClass，用于压力测试，装饰在用例类
    需要setUpClass和tearDownClass成对出现
    当setUpClass执行出错时，可以执行exec_func这个函数，在用例类里面定义这个exec_func函数时，建议使用类方法，用@classmethod装饰器
    """
    cls = None

    def decorator(func_or_cls):
        if inspect.isclass(func_or_cls):
            nonlocal cls  # 使用函数的外层(非全局)变量
            cls = func_or_cls
            setattr(func_or_cls, 'sc_tc_counts', 1)

            for name, func in list(func_or_cls.__dict__.items()):
                if name == 'setUpClass' or name == 'tearDownClass':
                    setattr(func_or_cls, name, decorator(func))
            return func_or_cls
        else:
            @wraps(func_or_cls)
            def wrapper():
                try:
                    if str(func_or_cls.__func__.__name__) == 'setUpClass':
                        if cls.sc_tc_counts == 1:
                            func_or_cls.__func__(cls)
                    elif str(func_or_cls.__func__.__name__) == 'tearDownClass':
                        if 'test_counts' in cls.unittest_attributes:
                            test_counts = cls.unittest_attributes['test_counts']
                        else:
                            test_counts = 1
                        if param_get_stop_exec_enable() or cls.sc_tc_counts == test_counts:
                            func_or_cls.__func__(cls)
                            cls.sc_tc_counts = 1  # 执行完tearDownClass，将test_counts重置为1
                        else:
                            cls.sc_tc_counts += 1
                except Exception as e:
                    try:
                        if exec_func:
                            print('\n{}unittest_sc_error_to_exec: {}{}\n'.format(
                                '-' * 20, str(exec_func), '-' * 20))

                        if not exec_func:
                            pass
                        elif isinstance(exec_func, classmethod):
                            exec_func.__func__(cls, *func_args, **func_kwargs)
                        elif inspect.isfunction(exec_func):
                            exec_func(*func_args, **func_kwargs)
                        elif isinstance(exec_func, str):
                            if exec_func.startswith('cls.') or exec_func.startswith('self.'):
                                config_get_and_call_nested_attribute(
                                    exec_func, cls, *func_args, **func_kwargs)
                            else:
                                config_get_and_call_nested_attribute(
                                    exec_func, None, *func_args, **func_kwargs)
                    except:
                        print(traceback.format_exc())

                    raise e
                return

            return wrapper

    if target:
        return decorator(target)
    else:
        return decorator


def unittest_exec_once_before_test(func, *func_args, sleep_time_after_func_exec=0, **func_kwargs):
    """
    重复多次执行同一个用例之前想只执行一次某些方法，可以使用该装饰器，可以用于压测
    注意：如果用于有ddt装饰的用例，同时测试多个用例，并且test_counts不止一遍，则最好使用exec_one_case_to_report_enable=True，
    这样会先把一个用例放在一起执行多遍和多组数据后，再执行其他用例，否则可能会因为先执行其他用例之后影响到该用例的执行

    如果要用于有ddt装饰的用例，那么该用例类需要指定测试用例名称只增加序号：@ddt.ddt(testNameFormat=ddt.TestNameFormat.INDEX_ONLY)
    或者用例类的ddt.ddt装饰器改为重写过的unittest_ddt_ddt,该装饰器方法会自动把用例名称后缀序号去掉。
    :param func: 要执行的函数或者函数名称，可以通过函数名称直接调用函数
    比如：device_web_reset_and_init or 'self.master_android_indoor_web.set_key_display_home_area'
    :param sleep_time_after_func_exec: 执行后等待延迟时间
    :param func_args: 要执行的函数的参数
    :param func_kwargs: 要执行的函数的参数
    :return:
    """

    def wrapper_func(test_func):
        @wraps(test_func)  # @wraps：避免被装饰函数自身的信息丢失
        def inner_func(self, *args, **kwargs):

            if not hasattr(self.__class__, 'unittest_attributes'):
                setattr(self.__class__, 'unittest_attributes', {})
            if 'test_counts' in self.__class__.unittest_attributes:
                test_counts = self.__class__.unittest_attributes['test_counts']
            else:
                test_counts = 1

            # 如果名称结尾是否为数字，认为是ddt添加的序号，将序号去除掉得到原始名称
            if self._testMethodName.split('_')[-1].isdigit():
                case_name = '_'.join(self._testMethodName.split('_')[0:-1])
            else:
                case_name = self._testMethodName
            test_counts_var_name = '%s_counts' % case_name
            test_total_counts_var_name = '%s_total_counts' % case_name
            before_test_enable_var_name = '%s_before_test_enable' % case_name
            after_test_enable_var_name = '%s_after_test_enable' % case_name
            self.__class__.unittest_attributes[before_test_enable_var_name] = True

            test_class_cases_list = list(
                filter(lambda x: not x.startswith("__") and not x.endswith("__") and x.startswith(
                    "test_") and callable(getattr(self.__class__, x)), dir(self.__class__)))
            # 获取用例执行多少遍总数
            if test_total_counts_var_name not in self.__class__.unittest_attributes:
                self.__class__.unittest_attributes[test_total_counts_var_name] = 0
                for x in test_class_cases_list:
                    if case_name in x:
                        self.__class__.unittest_attributes[test_total_counts_var_name] += 1

            # 每个用例名称有一个Counts计数
            if test_counts_var_name not in self.__class__.unittest_attributes:
                self.__class__.unittest_attributes[test_counts_var_name] = 1

            if self.__class__.unittest_attributes[test_counts_var_name] == 1:
                if isinstance(func, classmethod):
                    aklog_printf('unittest_exec_once_before_test: %s' % func.__func__.__name__)
                    func.__func__(self.__class__, *func_args, **func_kwargs)
                elif inspect.isfunction(func):
                    aklog_printf('unittest_exec_once_before_test: %s' % func.__name__)
                    # 判断函数的第一个参数是否为self，如果不是self，则不是类函数，执行时第一个参数去掉self
                    func_vars = func.__code__.co_varnames
                    if func_vars:
                        first_var = func_vars[0]
                    else:
                        first_var = None
                    if first_var == 'self':
                        func(self, *func_args, **func_kwargs)
                    else:
                        func(*func_args, **func_kwargs)
                elif isinstance(func, str):
                    if func.startswith('self.') or func.startswith('cls.'):
                        config_get_and_call_nested_attribute(
                            func, self, *func_args, **func_kwargs)
                    else:
                        config_get_and_call_nested_attribute(
                            func, None, *func_args, **func_kwargs)
                    # eval(func)(*func_args, **func_kwargs)  # 通过函数名称直接调用函数
                time.sleep(int(sleep_time_after_func_exec))
                if after_test_enable_var_name not in self.__class__.unittest_attributes:
                    # 如果test_counts=1只执行一遍，那么要删除test_counts_var_name属性，避免test_times重复多遍时出错
                    if test_counts == self.__class__.unittest_attributes[test_total_counts_var_name] == 1:
                        del self.__class__.unittest_attributes[test_counts_var_name]
                        del self.__class__.unittest_attributes[test_total_counts_var_name]
                        del self.__class__.unittest_attributes[before_test_enable_var_name]
                    else:
                        self.__class__.unittest_attributes[test_counts_var_name] += 1
            elif self.__class__.unittest_attributes[test_counts_var_name] \
                    == test_counts * self.__class__.unittest_attributes[test_total_counts_var_name] and \
                    after_test_enable_var_name not in self.__class__.unittest_attributes:
                del self.__class__.unittest_attributes[test_counts_var_name]
                del self.__class__.unittest_attributes[test_total_counts_var_name]
            elif after_test_enable_var_name not in self.__class__.unittest_attributes:
                self.__class__.unittest_attributes[test_counts_var_name] += 1
            result = test_func(self, *args, **kwargs)
            return result

        return inner_func

    return wrapper_func


def unittest_exec_once_after_test(func, *func_args, sleep_time_after_func_exec=0, **func_kwargs):
    """
    重复多次执行同一个用例，但只想执行一次某些方法，可以使用该装饰器，一般用于压测
    可以搭配unittest_exec_once_before_test使用，同时装饰一个用例

    注意：如果用于有ddt装饰的用例，同时测试多个用例，并且test_counts不止一遍，则最好使用exec_one_case_to_report_enable=True，
    这样会先把一个用例放在一起执行多遍和多组数据后，再执行其他用例，否则可能会因为还未执行指定方法，导致其他用例执行异常

    如果要用于有ddt装饰的用例，那么该用例类需要指定测试用例名称只增加序号：@ddt.ddt(testNameFormat=ddt.TestNameFormat.INDEX_ONLY)
    或者用例类的ddt.ddt装饰器改为重写过的unittest_ddt_ddt,该装饰器方法会自动把用例名称后缀序号去掉。
    :param func: 要执行的函数或者函数名称，可以通过函数名称直接调用函数
    比如：device_web_reset_and_init or 'self.master_android_indoor_web.set_key_display_home_area'
    :param sleep_time_after_func_exec: 执行后等待延迟时间
    :param func_args: 要执行的函数的参数
    :param func_kwargs: 要执行的函数的参数
    :return:
    """

    def wrapper_func(test_func):
        @wraps(test_func)  # @wraps：避免被装饰函数自身的信息丢失
        def inner_func(self, *args, **kwargs):

            if not hasattr(self.__class__, 'unittest_attributes'):
                setattr(self.__class__, 'unittest_attributes', {})
            if 'test_counts' in self.__class__.unittest_attributes:
                test_counts = self.__class__.unittest_attributes['test_counts']
            else:
                test_counts = 1
            # 如果名称结尾是数字，认为是ddt添加的序号，将序号去除掉得到原始名称
            if self._testMethodName.split('_')[-1].isdigit():
                case_name = '_'.join(self._testMethodName.split('_')[0:-1])
            else:
                case_name = self._testMethodName
            test_counts_var_name = '%s_counts' % case_name
            test_total_counts_var_name = '%s_total_counts' % case_name
            before_test_enable_var_name = '%s_before_test_enable' % case_name
            after_test_enable_var_name = '%s_after_test_enable' % case_name
            if after_test_enable_var_name not in self.__class__.unittest_attributes and \
                    before_test_enable_var_name in self.__class__.unittest_attributes:
                self.__class__.unittest_attributes[test_counts_var_name] = 1
            self.__class__.unittest_attributes[after_test_enable_var_name] = True

            test_class_cases_list = list(
                filter(lambda x: not x.startswith("__") and not x.endswith("__") and x.startswith(
                    "test_") and callable(getattr(self.__class__, x)), dir(self.__class__)))
            # 获取用例执行多少遍总数
            if test_total_counts_var_name not in self.__class__.unittest_attributes:
                self.__class__.unittest_attributes[test_total_counts_var_name] = 0
                for x in test_class_cases_list:
                    if case_name in x:
                        self.__class__.unittest_attributes[test_total_counts_var_name] += 1

            try:
                result = test_func(self, *args, **kwargs)
            except Exception:
                raise
            finally:
                # 每个用例名称有一个Counts计数
                if test_counts_var_name not in self.__class__.unittest_attributes:
                    self.__class__.unittest_attributes[test_counts_var_name] = 1

                if self.__class__.unittest_attributes[test_counts_var_name] == \
                        self.__class__.unittest_attributes[test_total_counts_var_name] * test_counts:
                    if isinstance(func, classmethod):
                        aklog_printf('unittest_exec_once_after_test: %s' % func.__func__.__name__)
                        func.__func__(self.__class__, *func_args, **func_kwargs)
                    elif inspect.isfunction(func):
                        aklog_printf('unittest_exec_once_after_test: %s' % func.__name__)
                        # 判断函数的第一个参数是否为self，如果不是self，则不是类函数，执行时第一个参数去掉self
                        func_vars = func.__code__.co_varnames
                        if func_vars:
                            first_var = func_vars[0]
                        else:
                            first_var = None
                        if first_var == 'self':
                            func(self, *func_args, **func_kwargs)
                        else:
                            func(*func_args, **func_kwargs)
                    elif isinstance(func, str):
                        if func.startswith('self.') or func.startswith('cls.'):
                            config_get_and_call_nested_attribute(
                                func, self, *func_args, **func_kwargs)
                        else:
                            config_get_and_call_nested_attribute(
                                func, None, *func_args, **func_kwargs)
                        # eval(func)(*func_args, **func_kwargs)  # 通过函数名称直接调用函数
                    time.sleep(int(sleep_time_after_func_exec))
                    del self.__class__.unittest_attributes[test_total_counts_var_name]
                    del self.__class__.unittest_attributes[test_counts_var_name]
                    del self.__class__.unittest_attributes[after_test_enable_var_name]
                else:
                    self.__class__.unittest_attributes[test_counts_var_name] += 1

            return result

        return inner_func

    return wrapper_func


def unittest_check_nap_time(start_time=None, end_time=None):
    """
    执行用例之前判断是否为午休时间或者暂停执行期间，如果是，则等待时间结束再继续执行
    可以装饰在用例类上面，整个用例类判断一次是否为暂停时间
    也可以装饰在特定用例上面
    如果该用例同时存在跳过执行装饰器，要将跳过装饰器放在该装饰器上面，否则会先等待再进行是否跳过判断
    """
    if not isinstance(start_time, str):
        if not g_nap_time_range:
            nap_start_time = config_get_value_from_ini_file('config', 'nap_start_time')
            nap_stop_time = config_get_value_from_ini_file('config', 'nap_stop_time')
            g_nap_time_range.append(nap_start_time)
            g_nap_time_range.append(nap_stop_time)
        start_time_str = g_nap_time_range[0]
    else:
        start_time_str = start_time
    if not isinstance(end_time, str):
        end_time_str = g_nap_time_range[1]
    else:
        end_time_str = end_time

    def decorator(func_or_cls):
        if inspect.isclass(func_or_cls):
            @wraps(func_or_cls)  # @wraps：避免被装饰函数自身的信息丢失
            def wrapper(*args, **kwargs):
                wait_time = judge_cur_time_within_time_range(start_time_str, end_time_str)
                if wait_time > 0:
                    aklog_printf('当前为午休或者暂停执行期间，等到 %s 之后再继续执行' % end_time_str)
                    time.sleep(wait_time)
                return func_or_cls(*args, **kwargs)

            return wrapper
        else:
            if not hasattr(func_or_cls, 'unittest_sleep'):
                setattr(func_or_cls, 'unittest_sleep', {'start_time': start_time_str,
                                                        'end_time': end_time_str})

            @wraps(func_or_cls)  # @wraps：避免被装饰函数自身的信息丢失
            def wrapper(*args, **kwargs):
                sleep_within_time_range(start_time_str, end_time_str)
                return func_or_cls(*args, **kwargs)

            return wrapper

    if callable(start_time):
        return decorator(start_time)
    else:
        return decorator


def unittest_ddt_mk_test_name(name, value, index=0, index_len=2, name_fmt=ddt.TestNameFormat.DEFAULT):
    """重写ddt.mk_test_name方法，只需使用unittest_ddt_ddt即可，不需要调用本方法"""

    # Add zeros before index to keep order
    index = "{0:0{1}}".format(index + 1, index_len)
    if name_fmt is ddt.TestNameFormat.INDEX_ONLY or not ddt.is_trivial(value):
        return "{0}_{1}".format(name, index)
    try:
        value = str(value)
    except UnicodeEncodeError:
        # fallback for python2
        value = value.encode('ascii', 'backslashreplace')
    test_name = "{0}_{1}_{2}".format(name, index, value)
    return re.sub(r'\W|^(?=\d)', '_', test_name)


def unittest_ddt_ddt(arg=None, **kwargs):
    """
    使用方法：用例类的@ddt.ddt装饰器改为@unittest_ddt_ddt，
    说明：当testdata list的长度超过10，并且同一个用例里面存在多个不同长度的testdata，
    那么会使用最后一个testdata的长度，导致加载用例时长度超过10的testdata对应用例的序号不是01、02这样，变成1 10 2 3这样的顺序。
    重写ddt.ddt方法，
    并将用例名称后缀改为默认只有序号，不会加上testdata的值，
    可以解决unittest_exec_once_before_test装饰器在使用ddt之后失效的问题。
    """
    fmt_test_name = kwargs.get("testNameFormat", ddt.TestNameFormat.INDEX_ONLY)

    def wrapper(cls):
        for name, func in list(cls.__dict__.items()):
            if hasattr(func, ddt.DATA_ATTR):
                # print(getattr(func, ddt.DATA_ATTR))
                index_len = len(str(len(getattr(func, ddt.DATA_ATTR))))
                # print(index_len)
                for i, v in enumerate(getattr(func, ddt.DATA_ATTR)):
                    test_name = unittest_ddt_mk_test_name(
                        name,
                        getattr(v, "__name__", v),
                        i,
                        index_len,
                        fmt_test_name
                    )
                    test_data_docstring = ddt._get_test_data_docstring(func, v)
                    if hasattr(func, ddt.UNPACK_ATTR):
                        if isinstance(v, tuple) or isinstance(v, list):
                            ddt.add_test(
                                cls,
                                test_name,
                                test_data_docstring,
                                func,
                                *v
                            )
                        else:
                            # unpack dictionary
                            ddt.add_test(
                                cls,
                                test_name,
                                test_data_docstring,
                                func,
                                **v
                            )
                    else:
                        ddt.add_test(cls, test_name, test_data_docstring, func, v)
                delattr(cls, name)
            elif hasattr(func, ddt.FILE_ATTR):
                file_attr = getattr(func, ddt.FILE_ATTR)
                ddt.process_file_data(cls, name, func, file_attr)
                delattr(cls, name)
        return cls

    # ``arg`` is the unittest's test class when decorating with ``@ddt`` while
    # it is ``None`` when decorating a test class with ``@ddt(k=v)``.
    return wrapper(arg) if inspect.isclass(arg) else wrapper


def _assert_fail(val):
    """判断val是否为Fail"""
    # bool型为False
    if isinstance(val, bool):
        if val:
            return False
        else:
            return True
    # 错误码不为零
    error_codes = [2, 1, 0, -1, -2]
    if isinstance(val, int) and val in error_codes:
        if val != 0:
            return True
        else:
            return False
    # 空list/dict/str
    if not bool(val):
        return True
    # warn为警告
    if val == 'warn':
        return True
    return False


def unittest_add_results(result: list, *devices_instance, assert_enable=True, is_raise=False, re_shot=True) -> list:
    """
    注意：该方法主要用于Control层用例层的业务流操作方法添加检查项，作为产品问题断言

    添加检查结果到results，同时错误时打印log，如果需要截图，则可以传入设备对象
    一般只在Control模块和用例中使用，将结果添加到断言列表。
    如果检查的结果True或False都有可能作为预期结果，那么最好不要在操作方法里使用该方法。
    可以在操作方法里面使用warn来作为警告检查项，主要用于页面切换方法，常规路径无法进入然后做了异常恢复动作时使用
    Args:
        result (list): 当前的检查结果： [ret, '具体的错误或成功信息，会作为断言的message，显示在报告的失败项', '额外上下文信息，便于问题定位']
            result[0]: 可以填0/1/-1/-2，0表示为断言成功，1表示产品问题，负数表示脚本或环境问题
        *devices_instance (object): 设备对象，比如：panel, belahome， 主要用于截图
        assert_enable (bool): 是否添加到断言结果，为False表示只打印错误或警告日志以及截图
        is_raise (bool): 是否立即抛出断言异常
        re_shot (bool): 是否重新截图，如果为False时，要确认是要保存前一个步骤的截图
    Returns:
        result
    """
    if not isinstance(result, list):
        raise ValueError(f"{result} 不是list类型")

    if _assert_fail(result[0]):
        if len(result) < 2:
            result.append('未知错误，请补充错误说明')
        elif not result[1]:
            result[1] = '未知错误，请补充错误说明'

        # 将device_name写入到result描述中
        f_back_frame = inspect.currentframe().f_back
        param_dict = f_back_frame.f_locals
        if 'self' in param_dict:
            device_fullname = getattr(param_dict['self'], 'device_fullname', '')
            device_name = getattr(param_dict['self'], 'device_name', '')
            if device_fullname and device_fullname not in result[1]:
                result[1] = '{} {}'.format(device_fullname, result[1])
            elif device_name and device_name not in result[1]:
                result[1] = '[{}] {}'.format(device_name, result[1])

        if result[0] == 'warn':
            result[1] = f'【警告】{result[1]}'
            aklog_printf(result[1], log_level=3, back_depth=3)  # aklog_warn
        elif result[0] == -2:
            result[1] = f'【环境】{result[1]}'
            aklog_printf(result[1], log_level=2, back_depth=3)  # aklog_error
        elif result[0] == -1:
            result[1] = f'【脚本】{result[1]}'
            aklog_printf(result[1], log_level=2, back_depth=3)  # aklog_error
        else:
            result[1] = f'【产品】{result[1]}'
            aklog_printf(result[1], log_level=2, back_depth=3)  # aklog_error

        # 其他要打印的上下文信息
        if len(result) > 2:
            aklog_printf(result[2], log_level=5, back_depth=3)  # aklog_debug

        # 设备截图
        if devices_instance:
            for device in devices_instance:
                if hasattr(device, 'screen_shot'):
                    if 're_shot' in inspect.signature(device.screen_shot).parameters:
                        device.screen_shot(re_shot)
                    else:
                        device.screen_shot()
                elif hasattr(device, 'app') and hasattr(device.app, 'screen_shot'):
                    if 're_shot' in inspect.signature(device.app.screen_shot).parameters:
                        device.app.screen_shot(re_shot)
                    else:
                        device.app.screen_shot()

    if assert_enable:
        param_append_test_results(result)

        # 在过程中添加断言信息时，直接将异常抛出，结束当前用例执行
        if is_raise and param_get_test_results():
            test_case = unittest.TestCase()
            verificationErrors = []
            for _result in param_get_test_results():
                try:
                    if _assert_fail(_result[0]):
                        test_case.assertTrue(False, _result[1])
                except AssertionError as e:
                    verificationErrors.append(e)

            new_verificationErrors = []
            for error in verificationErrors:
                if 'warning : 【警告】' not in str(error):
                    new_verificationErrors.append(error)
            if new_verificationErrors:
                # 将警告类断言移到列表靠后位置，第一项要为产品或脚本问题，如果只存在警告类断言，将不抛出异常，最终会断言成功
                for error in verificationErrors:
                    if 'warning : 【警告】' in str(error):
                        new_verificationErrors.append(error)
                test_case.assertListEqual(new_verificationErrors, [])

    return result


def unittest_results(result: list, *devices_instance, assert_enable=True, is_raise=False, re_shot=True) -> list:
    """
        注意：该方法主要用于Flow层的业务流操作方法添加检查项，最终会作为警告显示在测试报告里面，属于脚本或者环境问题

        添加检查结果到results，同时错误时打印log，如果需要截图，则可以传入设备对象
        一般只在Control模块和用例中使用，将结果添加到断言列表。
        如果检查的结果True或False都有可能作为预期结果，那么最好不要在操作方法里使用该方法。
        可以在操作方法里面使用warn来作为警告检查项，主要用于页面切换方法，常规路径无法进入然后做了异常恢复动作时使用
        Args:
            result (list): 当前的检查结果： [ret, '具体的错误或成功信息，会作为断言的message，显示在报告的失败项', '额外上下文信息，便于问题定位']
                result[0]: 可以填0/1/-1/-2，0表示为断言成功，1表示产品问题，负数表示脚本或环境问题
            *devices_instance (object): 设备对象，比如：panel, belahome， 主要用于截图
            assert_enable (bool): 是否添加到断言结果，为False表示只打印错误或警告日志以及截图
            is_raise (bool): 是否立即抛出断言异常
            re_shot (bool): 是否重新截图，如果为False时，要确认是要保存前一个步骤的截图
        Returns:
            result
        """
    if not isinstance(result, list) or len(result) == 0:
        raise ValueError(f"result: {result}, 不是list类型或者list为空")

    if _assert_fail(result[0]):
        if len(result) < 2:
            result.append('未知错误，请补充错误说明')
        elif not result[1]:
            result[1] = '未知错误，请补充错误说明'

        # 将device_name写入到result描述中
        f_back_frame = inspect.currentframe().f_back
        param_dict = f_back_frame.f_locals
        if 'self' in param_dict:
            device_fullname = getattr(param_dict['self'], 'device_fullname', '')
            device_name = getattr(param_dict['self'], 'device_name', '')
            if device_fullname and device_fullname not in result[1]:
                result[1] = '{} {}'.format(device_fullname, result[1])
            elif device_name and device_name not in result[1]:
                result[1] = '[{}] {}'.format(device_name, result[1])

        if result[0] == 'warn':
            result[1] = f'【警告】{result[1]}'
            aklog_printf(result[1], log_level=3, back_depth=3)  # aklog_warn
        elif result[0] == -2:
            result[1] = f'【环境】{result[1]}'
            aklog_printf(result[1], log_level=2, back_depth=3)  # aklog_error
        elif result[0] == -1:
            result[1] = f'【脚本】{result[1]}'
            aklog_printf(result[1], log_level=2, back_depth=3)  # aklog_error
        else:
            result[1] = f'【产品】{result[1]}'
            aklog_printf(result[1], log_level=2, back_depth=3)  # aklog_error

        # 其他要打印的上下文信息
        if len(result) > 2:
            aklog_printf(result[2], log_level=5, back_depth=3)  # aklog_debug

        # 设备截图
        if devices_instance:
            for device in devices_instance:
                if hasattr(device, 'screen_shot'):
                    if 're_shot' in inspect.signature(device.screen_shot).parameters:
                        device.screen_shot(re_shot)
                    else:
                        device.screen_shot()
                elif hasattr(device, 'app') and hasattr(device.app, 'screen_shot'):
                    if 're_shot' in inspect.signature(device.app.screen_shot).parameters:
                        device.app.screen_shot(re_shot)
                    else:
                        device.app.screen_shot()

        # 结果为False时，才添加到断言列表
        if assert_enable:
            param_append_test_results(result)

            # 在过程中添加断言信息时，直接将异常抛出，结束当前用例执行
            if is_raise and param_get_test_results():
                test_case = unittest.TestCase()
                verificationErrors = []
                for _result in param_get_test_results():
                    try:
                        if _assert_fail(_result[0]):
                            test_case.assertTrue(False, _result[1])
                    except AssertionError as e:
                        verificationErrors.append(e)

                new_verificationErrors = []
                for error in verificationErrors:
                    if 'warning : 【警告】' not in str(error):
                        new_verificationErrors.append(error)
                if new_verificationErrors:
                    # 将警告类断言移到列表靠后位置，第一项要为产品或脚本问题，如果只存在警告类断言，将不抛出异常，最终会断言成功
                    for error in verificationErrors:
                        if 'warning : 【警告】' in str(error):
                            new_verificationErrors.append(error)
                    test_case.assertListEqual(new_verificationErrors, [])
    else:
        # 当结果为True时，打印正常日志，正常日志最好不要包含'失败', '错误', '异常', '不存在', '不正确'等词语
        if len(result) < 2 or not result[1]:
            pass
        elif all(keyword not in str(result[1]).lower()
                 for keyword in
                 ['失败', '错误', '异常', '不存在', '不正确', '未', '没有', '仍有',
                  'error', 'fail', 'not found', 'not_found']):
            aklog_printf(result[1], log_level=4, back_depth=3)  # aklog_info

    return result


class ak_unittest_test_case(unittest.TestCase):
    """
    重写断言，捕获断言异常，然后将异常信息传给verificationErrors，
    适用于一个用例多个断言，保证多个断言都会执行到，而不会因为断言失败导致之后的语句没有执行
    如果用例中需要setUp和tearDown时，可以用super().setUp()方式继承这个重写
    例如：
    def setUp(self):
        super().setUp()
        ...
    is_raise: 是否直接抛出异常，该参数一般用于用例的第一条断言设置为True，表明第一条断言失败就直接抛出异常，不再继续执行该条用例后续语句
        为True时，断言失败直接抛出异常，结束退出该条用例测试，不再继续执行该条用例后续语句
        为False时，会执行该用例所有断言，并捕获所有断言失败结果，最后再统一验证断言结果
    """

    maxDiff = None

    def run(self, result=None):
        if result is None:
            result = self.defaultTestResult()
            startTestRun = getattr(result, 'startTestRun', None)
            stopTestRun = getattr(result, 'stopTestRun', None)
            if startTestRun is not None:
                startTestRun()
        else:
            stopTestRun = None

        result.startTest(self)
        try:
            testMethod = getattr(self, self._testMethodName)
            # 先把警告__unittest_expecting_warning__移除
            if hasattr(testMethod, '__unittest_expecting_warning__'):
                delattr(testMethod.__func__, '__unittest_expecting_warning__')

            if (getattr(self.__class__, "__unittest_skip__", False) or
                    getattr(testMethod, "__unittest_skip__", False)):
                # If the class or method was skipped.
                skip_why = (getattr(self.__class__, '__unittest_skip_why__', '')
                            or getattr(testMethod, '__unittest_skip_why__', ''))
                _addSkip(result, self, skip_why)
                return result

            expecting_failure = (
                    getattr(self, "__unittest_expecting_failure__", False) or
                    getattr(testMethod, "__unittest_expecting_failure__", False)
            )
            outcome = _Outcome(result)
            start_time = time.perf_counter()
            try:
                self._outcome = outcome

                with outcome.testPartExecutor(self):
                    self._callSetUp()
                if outcome.success:
                    outcome.expecting_failure = expecting_failure
                    with outcome.testPartExecutor(self):
                        self._callTestMethod(testMethod)
                    outcome.expecting_failure = False
                    with outcome.testPartExecutor(self):
                        self._callTearDown()
                self.doCleanups()
                self._addDuration(result, (time.perf_counter() - start_time))

                if outcome.success:
                    if expecting_failure:
                        if outcome.expectedFailure:
                            self._addExpectedFailure(result, outcome.expectedFailure)
                        else:
                            self._addUnexpectedSuccess(result)
                    else:
                        expecting_warning_list = getattr(testMethod,
                                                         '__unittest_expecting_warning__', False)
                        if expecting_warning_list and hasattr(result, 'addWarning'):
                            try:
                                super().assertListEqual(expecting_warning_list, [])
                            except AssertionError as e:
                                result.addWarning(self, (testMethod, e, None))
                        else:
                            result.addSuccess(self)

                return result
            finally:
                # explicitly break reference cycle:
                # outcome.expectedFailure -> frame -> outcome -> outcome.expectedFailure
                outcome.expectedFailure = None
                outcome = None

                # clear the outcome, no more needed
                self._outcome = None

        finally:
            result.stopTest(self)
            if stopTestRun is not None:
                stopTestRun()

    def save_syslog(self, *devices_instance_name):
        """
        将设备的log导出保存到Result目录，可以配合装饰器unittest_fail_to_exec使用，用于执行失败时保存各个设备的log。
        @unittest_fail_to_exec(save_syslog, 'master_smartpanel', 'master_smartpanel_web', 'slave1_hyperpanel_web')

        用例类那边需要继承该方法：
        def save_syslog(self, *devices_instance_name):
            super().save_syslog(*devices_instance_name)
        """
        aklog_debug()
        try:
            func_list = []
            interval = 1

            # 如果传入的参数不是设备对象名称，而是对象本身，则直接调用导出log方法
            for instance_name in devices_instance_name:
                if instance_name != 'device_instance_list':
                    continue
                device_instance_list = getattr(self, 'device_instance_list', None)
                if not device_instance_list:
                    continue
                for device_instance in device_instance_list:
                    if not device_instance:
                        continue

                    # 判断导出方式
                    device_name = getattr(device_instance, 'device_name', '')
                    export_type = None
                    if hasattr(device_instance, 'device_config') and hasattr(
                            device_instance.device_config, 'get_default_export_syslog_type'):
                        export_type = device_instance.device_config.get_default_export_syslog_type()
                    # 仅当导出方式为upload时，才判断失败次数
                    if export_type == "upload":
                        fail_case_count = param_get_fail_case_count().get(self._testMethodName)
                        case_fail_export_log_count = config_get_value_from_ini_file(
                            'config', 'case_fail_export_log_count')
                        if case_fail_export_log_count is None:
                            case_fail_export_log_count = 0
                        case_fail_export_log_count = int(case_fail_export_log_count)
                        # 0表示不限制
                        if fail_case_count and 0 < case_fail_export_log_count <= fail_case_count:
                            aklog_warn(
                                f'{self._testMethodName} 用例失败次数超过 {case_fail_export_log_count} 次，'
                                f'设备 {device_name} 不再上传log')
                            continue  # 跳过本设备

                    # 导出syslog，logcat或者cat /tmp/Messages，或者设备网页
                    func = (getattr(device_instance, 'export_syslog_to_result', None)
                            or getattr(device_instance, 'upload_log_by_tln_or_ssh', None)
                            or getattr(device_instance, 'export_syslog_to_results_dir', None)
                            or getattr(device_instance, 'export_syslog_to_results_dir_by_tln_or_ssh', None))
                    if func is None:
                        device_instance_web = (getattr(device_instance, 'web_inf', None)
                                               or getattr(device_instance, 'web', None)
                                               or getattr(device_instance, 'browser', None))
                        if device_instance_web:
                            func = (getattr(device_instance_web, 'export_syslog_to_result', None)
                                    or getattr(device_instance_web, 'upload_log_by_tln_or_ssh', None)
                                    or getattr(device_instance_web, 'export_syslog_to_results_dir', None)
                                    or getattr(device_instance_web, 'export_syslog_to_results_dir_by_tln_or_ssh', None))
                    if func is not None:
                        func_list.append((func, (self._testMethodName,)))

            if func_list:
                thread_start_with_join(*func_list, interval=interval)
                return True

            # 先给devices_instance_name排序，有些机型导出log的方式可能有多种，比如adb方式和logcat导出，
            # base实例下的方法先去获取log，之后才是web实例下的方法
            devices_instance_name_list = list(devices_instance_name)
            devices_instance_name_list_new = []
            for name in devices_instance_name_list:
                if name.endswith('_web') or name.endswith('_browser'):
                    base_instance_name = name.replace('_web', '').replace('_browser', '')
                    if base_instance_name in devices_instance_name_list and \
                            base_instance_name not in devices_instance_name_list_new:
                        devices_instance_name_list_new.append(base_instance_name)
                        devices_instance_name_list_new.insert(
                            devices_instance_name_list_new.index(base_instance_name) + 1,
                            name)
                    else:
                        devices_instance_name_list_new.append(name)
                elif name not in devices_instance_name_list_new:
                    devices_instance_name_list_new.append(name)

            syslog_device_name_list = []
            for device_instance_name in devices_instance_name_list_new:
                if not hasattr(self, device_instance_name):
                    aklog_warn('%s 未初始化' % device_instance_name)
                    continue
                device_instance = getattr(self, device_instance_name, None)
                if device_instance is None:
                    aklog_warn('%s 未初始化' % device_instance_name)
                    continue

                device_name = getattr(device_instance, 'device_name', '')
                if device_name and device_name in syslog_device_name_list:
                    continue

                # 判断导出方式
                export_type = None
                if hasattr(device_instance, 'device_config') and hasattr(
                        device_instance.device_config, 'get_default_export_syslog_type'):
                    export_type = device_instance.device_config.get_default_export_syslog_type()
                # 仅当导出方式为upload时，才判断失败次数
                if export_type == "upload":
                    fail_case_count = param_get_fail_case_count().get(self._testMethodName)
                    case_fail_export_log_count = config_get_value_from_ini_file(
                        'config', 'case_fail_export_log_count')
                    if case_fail_export_log_count is None:
                        case_fail_export_log_count = 0
                    case_fail_export_log_count = int(case_fail_export_log_count)
                    # 0表示不限制
                    if fail_case_count and 0 < case_fail_export_log_count <= fail_case_count:
                        aklog_warn(
                            f'{self._testMethodName} 用例失败次数超过 {case_fail_export_log_count} 次，'
                            f'设备 {device_name} 不再上传log')
                        continue  # 跳过本设备

                # 导出syslog，logcat或者cat /tmp/Messages，或者设备网页
                func = (getattr(device_instance, 'export_syslog_to_result', None)
                        or getattr(device_instance, 'upload_log_by_tln_or_ssh', None)
                        or getattr(device_instance, 'export_syslog_to_results_dir', None)
                        or getattr(device_instance, 'export_syslog_to_results_dir_by_tln_or_ssh', None))
                if func is None:
                    device_instance_web = (getattr(device_instance, 'web_inf', None)
                                           or getattr(device_instance, 'web', None)
                                           or getattr(device_instance, 'browser', None))
                    if device_instance_web:
                        func = (getattr(device_instance_web, 'export_syslog_to_result', None)
                                or getattr(device_instance_web, 'upload_log_by_tln_or_ssh', None)
                                or getattr(device_instance_web, 'export_syslog_to_results_dir', None)
                                or getattr(device_instance_web, 'export_syslog_to_results_dir_by_tln_or_ssh', None))
                if func is not None:
                    func_list.append((func, (self._testMethodName,)))
                if device_name:
                    syslog_device_name_list.append(device_name)

            thread_start_with_join(*func_list, interval=interval)
            return True
        except:
            aklog_error('保存log失败')
            aklog_debug(traceback.format_exc())
            return False

    def screen_shot(self, *devices_instance_name):
        """
        截图，可以配合装饰器unittest_fail_to_exec或者unittest_fail_to_exec_on_teardown使用，用于执行失败时保存截图。
        @unittest_fail_to_exec(screen_shot, 'master_smartpanel', 'master_smartpanel_web', 'slave1_hyperpanel_web')
        @unittest_fail_to_exec_on_teardown(screen_shot, 'master_smartpanel', 'slave1_hyperpanel_web')
        用例类那边需要继承该方法：
        def screen_shot(self, *devices_instance_name):
            super().screen_shot(*devices_instance_name)
        """
        aklog_debug()
        try:
            func_list = []
            for device_instance_name in devices_instance_name:
                if not hasattr(self, device_instance_name):
                    aklog_printf('%s 未初始化' % device_instance_name)
                    continue
                device_instance = getattr(self, device_instance_name)
                if device_instance is None:
                    aklog_printf('%s 未初始化' % device_instance_name)
                    continue
                if hasattr(device_instance, 'screen_shot'):
                    # 最好在机型base或者web基类里面添加screen_shot方法
                    func = device_instance.screen_shot
                    func_list.append(func)
                elif hasattr(device_instance, 'app'):
                    device_app = device_instance.app
                    if hasattr(device_app, 'screen_shot'):
                        func = device_app.screen_shot
                        func_list.append(func)
                elif hasattr(device_instance, 'browser'):
                    device_web = device_instance.browser
                    if hasattr(device_web, 'screen_shot'):
                        func = device_web.screen_shot
                        func_list.append(func)
                elif hasattr(device_instance, 'web'):
                    device_web = device_instance.web
                    if hasattr(device_web, 'screen_shot'):
                        func = device_web.screen_shot
                        func_list.append(func)

            thread_start_with_join(*func_list)
            return True
        except:
            aklog_printf('保存截图失败')
            aklog_printf(traceback.format_exc())
            return False

    def save_pcap(self, *devices_instance_name):
        """
        将设备导出的PCAP抓包文件保存到Result目录，可以配合装饰器unittest_fail_to_exec使用，用于执行失败时保存各个设备的抓包。
        @unittest_fail_to_exec(save_pcap, 'master_smartpanel_web', 'slave1_hyperpanel_web')

        用例类那边需要继承该方法：
        def save_pcap(self, *devices_instance_name):
            super().save_pcap(*devices_instance_name)
        """
        aklog_debug()
        try:
            func_list = []

            # 如果传入的参数不是设备对象名称，而是对象本身，则直接调用导出log方法
            for instance_name in devices_instance_name:
                if instance_name == 'device_instance_list':
                    device_instance_list = getattr(self, 'device_instance_list', None)
                    if not device_instance_list:
                        continue
                    for device_instance in device_instance_list:
                        if not device_instance:
                            continue
                        # 导出syslog，logcat或者cat /tmp/Messages，或者设备网页
                        if hasattr(device_instance, 'save_pcap_to_results_dir'):
                            func = device_instance.save_pcap_to_results_dir
                            func_list.append((func, (self._testMethodName,)))
                        elif (hasattr(device_instance, 'web_inf')
                              and hasattr(device_instance.web_inf, 'save_pcap_to_results_dir')):
                            func = device_instance.web_inf.save_pcap_to_results_dir
                            func_list.append((func, (self._testMethodName,)))
                        elif (hasattr(device_instance, 'web')
                              and hasattr(device_instance.web, 'save_pcap_to_results_dir')):
                            func = device_instance.web.save_pcap_to_results_dir
                            func_list.append((func, (self._testMethodName,)))

            if func_list:
                thread_start_with_join(*func_list, interval=1)
                return True

            for device_instance_name in devices_instance_name:
                if not hasattr(self, device_instance_name):
                    aklog_printf('%s 未初始化' % device_instance_name)
                    continue
                device_instance = getattr(self, device_instance_name)
                if device_instance is None:
                    aklog_printf('%s 未初始化' % device_instance_name)
                    continue
                if hasattr(device_instance, 'save_pcap_to_results_dir'):
                    func = device_instance.save_pcap_to_results_dir
                    func_list.append((func, (self._testMethodName,)))
                elif hasattr(device_instance, 'browser'):
                    device_web = device_instance.browser
                    if hasattr(device_web, 'save_pcap_to_results_dir'):
                        func = device_instance.save_pcap_to_results_dir
                        func_list.append((func, (self._testMethodName,)))
                elif hasattr(device_instance, 'web'):
                    device_web = device_instance.web
                    if hasattr(device_web, 'save_pcap_to_results_dir'):
                        func = device_instance.save_pcap_to_results_dir
                        func_list.append((func, (self._testMethodName,)))

            thread_start_with_join(*func_list)
            return True
        except:
            aklog_printf('保存抓包文件失败')
            aklog_printf(traceback.format_exc())
            return False

    def save_syslog_pcap(self, *devices_instance_name):
        self.save_pcap(*devices_instance_name)
        self.save_syslog(*devices_instance_name)

    def screen_shot_and_save_syslog(self, *devices_instance_name):
        """
        用例类那边需要继承该方法：
        def screen_shot_and_save_syslog(self, *devices_instance_name):
            super().screen_shot_and_save_syslog(*devices_instance_name)
        配合unittest_fail_to_exec或者unittest_fail_to_exec_on_teardown使用：
        @unittest_fail_to_exec_on_teardown(screen_shot_and_save_syslog, 'master_android_hyperpanel')
        @unittest_fail_to_exec(screen_shot_and_save_syslog, 'master_android_hyperpanel')
        """
        self.screen_shot(*devices_instance_name)
        self.save_syslog(*devices_instance_name)

    def setUp(self):
        """
        用例类那边需要继承该方法：
        def setUp(self):
            super().setUp()
        """
        time.sleep(0.01)
        aklog_printf("%s, %s, setUp" % (self.__class__.__name__, self._testMethodName))
        self.imgs = []
        self.verificationErrors = []
        param_reset_screenshots_imgs()
        param_reset_test_results()
        if hasattr(self, 'device_instance_list') and isinstance(self.device_instance_list, list):
            self.device_instance_list.clear()

    def tearDown(self):
        """
        用例类那边需要继承该方法：
        def tearDown(self):
            super().tearDown()
        """
        time.sleep(0.01)
        aklog_printf("%s, %s, tearDown" % (self.__class__.__name__, self._testMethodName))
        self.imgs.extend(param_get_screenshots_imgs())
        if param_get_test_results():
            self.assertResultList()
        if config_set_stop_exec_enable():
            setattr(self.__class__, '__ak_unittest_skip__', True)
            setattr(self.__class__, '__ak_unittest_skip_why__', '准备退出执行')
        new_verificationErrors = []
        for error in self.verificationErrors:
            if 'warning : 【警告】' not in str(error):
                new_verificationErrors.append(error)
        if new_verificationErrors:
            # 将警告类断言移到列表靠后位置，第一项要为产品或脚本问题
            for error in self.verificationErrors:
                if 'warning : 【警告】' in str(error):
                    new_verificationErrors.append(error)
            super().assertListEqual(new_verificationErrors, [])

    def assertTrue(self, expr, msg=None, is_raise=False):
        """
        is_raise: 是否直接抛出异常，
        为True时，断言失败直接抛出异常，结束退出该条用例测试，不再继续执行，
        为False时，会执行该用例所有断言
        """
        try:
            super().assertTrue(expr, msg)
        except AssertionError as e:
            if is_raise:
                raise e
            self.verificationErrors.append(e)

    def assertFalse(self, expr, msg=None, is_raise=False):
        try:
            super().assertFalse(expr, msg)
        except AssertionError as e:
            if is_raise:
                raise e
            self.verificationErrors.append(e)

    def assertEqual(self, first, second, msg=None, is_raise=False):
        try:
            super().assertEqual(first, second, msg)
        except AssertionError as e:
            if is_raise:
                raise e
            self.verificationErrors.append(e)

    def assertNotEqual(self, first, second, msg=None, is_raise=False):
        try:
            super().assertNotEqual(first, second, msg)
        except AssertionError as e:
            if is_raise:
                raise e
            self.verificationErrors.append(e)

    def assertIsNone(self, expr, msg=None, is_raise=False):
        try:
            super().assertIsNone(expr, msg)
        except AssertionError as e:
            if is_raise:
                raise e
            self.verificationErrors.append(e)

    def assertIsNotNone(self, expr, msg=None, is_raise=False):
        try:
            super().assertIsNotNone(expr, msg)
        except AssertionError as e:
            if is_raise:
                raise e
            self.verificationErrors.append(e)

    def assertIs(self, first, second, msg=None, is_raise=False):
        try:
            super().assertIs(first, second, msg)
        except AssertionError as e:
            if is_raise:
                raise e
            self.verificationErrors.append(e)

    def assertIsNot(self, first, second, msg=None, is_raise=False):
        try:
            super().assertIsNot(first, second, msg)
        except AssertionError as e:
            if is_raise:
                raise e
            self.verificationErrors.append(e)

    def assertIn(self, member, container, msg=None, is_raise=False):
        try:
            super().assertIn(member, container, msg)
        except AssertionError as e:
            if is_raise:
                raise e
            self.verificationErrors.append(e)

    def assertNotIn(self, member, container, msg=None, is_raise=False):
        try:
            super().assertNotIn(member, container, msg)
        except AssertionError as e:
            if is_raise:
                raise e
            self.verificationErrors.append(e)

    def assertAlmostEqual(self, first, second, places=None, msg=None, delta=None, is_raise=False):
        try:
            super().assertAlmostEqual(first, second, places, msg, delta)
        except AssertionError as e:
            if is_raise:
                raise e
            self.verificationErrors.append(e)

    def assertNotAlmostEqual(self, first, second, places=None, msg=None, delta=None, is_raise=False):
        try:
            super().assertNotAlmostEqual(first, second, places, msg, delta)
        except AssertionError as e:
            if is_raise:
                raise e
            self.verificationErrors.append(e)

    def assertListEqual(self, first, second, msg=None, is_raise=False):
        try:
            super().assertListEqual(first, second, msg)
        except AssertionError as e:
            if is_raise:
                raise e
            self.verificationErrors.append(e)

    def assertTupleEqual(self, tuple1, tuple2, msg=None, is_raise=False):
        try:
            super().assertTupleEqual(tuple1, tuple2, msg)
        except AssertionError as e:
            if is_raise:
                raise e
            self.verificationErrors.append(e)

    def assertDictEqual(self, d1, d2, msg=None, is_raise=False):
        try:
            super().assertDictEqual(d1, d2, msg)
        except AssertionError as e:
            if is_raise:
                raise e
            self.verificationErrors.append(e)

    def assertLess(self, a, b, msg=None, is_raise=False):
        try:
            super().assertLess(a, b, msg)
        except AssertionError as e:
            if is_raise:
                raise e
            self.verificationErrors.append(e)

    def assertLessEqual(self, a, b, msg=None, is_raise=False):
        try:
            super().assertLessEqual(a, b, msg)
        except AssertionError as e:
            if is_raise:
                raise e
            self.verificationErrors.append(e)

    def assertGreater(self, a, b, msg=None, is_raise=False):
        try:
            super().assertGreater(a, b, msg)
        except AssertionError as e:
            if is_raise:
                raise e
            self.verificationErrors.append(e)

    def assertGreaterEqual(self, a, b, msg=None, is_raise=False):
        try:
            super().assertGreaterEqual(a, b, msg)
        except AssertionError as e:
            if is_raise:
                raise e
            self.verificationErrors.append(e)

    def assertIsInstance(self, obj, cls, msg=None, is_raise=False):
        try:
            super().assertIsInstance(obj, cls, msg)
        except AssertionError as e:
            if is_raise:
                raise e
            self.verificationErrors.append(e)

    def assertNotIsInstance(self, obj, cls, msg=None, is_raise=False):
        try:
            super().assertNotIsInstance(obj, cls, msg)
        except AssertionError as e:
            if is_raise:
                raise e
            self.verificationErrors.append(e)

    def assertResultList(self, results=None, is_raise=False):
        """
        list results结果断言
        Args:
            results (list): 每个元素也是一个list, 第一个元素为True/False，第二个为msg，第三个为补充说明， 比如：
                results = [
                    [True, 'xxx错误']
                ]
            is_raise (bool): 是否直接抛出异常，
                为True时，断言失败直接抛出异常，结束退出该条用例测试，不再继续执行，为False时，会执行该用例所有断言
        """
        if not results:
            # 需要在操作步骤和结果检查方法上使用unittest_add_results
            results = param_get_test_results()
        for result in results:
            if not isinstance(result, list):
                raise ValueError(f"{result} 不是list类型")

            # 第一个元素为True/False，第二个为msg，第三个为补充说明
            try:
                if len(result) == 1:
                    result.append('未知错误，请补充错误说明')
                # 如果第一个为字符串warn，说明该结果为警告项
                if result[0] == 'warn':
                    testMethod = getattr(self, self._testMethodName)
                    if not hasattr(testMethod, '__unittest_expecting_warning__'):
                        setattr(testMethod.__func__, '__unittest_expecting_warning__', [])
                    warning_assertion = AssertionError(f'warning : {result[1]}')
                    testMethod.__unittest_expecting_warning__.append(warning_assertion)
                    if warning_assertion not in self.verificationErrors:
                        self.verificationErrors.append(warning_assertion)
                elif _assert_fail(result[0]):
                    super().assertTrue(False, result[1])
            except AssertionError as e:
                self.verificationErrors.append(e)

        if is_raise:
            new_verificationErrors = []
            for error in self.verificationErrors:
                if 'warning : 【警告】' not in str(error):
                    new_verificationErrors.append(error)
            if new_verificationErrors:
                # 将警告类断言移到列表靠后位置，第一项要为产品或脚本问题
                for error in self.verificationErrors:
                    if 'warning : 【警告】' in str(error):
                        new_verificationErrors.append(error)
                super().assertListEqual(new_verificationErrors, [])
        param_reset_test_results()


class AK_unittest_screenshot(unittest.TestCase):
    """failed execute faildump automatically"""

    def assertTrue(self, expr, msg=None, is_raise=True):
        """
        is_raise: 是否直接抛出异常，
            为True时，断言失败直接抛出异常，结束退出该条用例测试，不再继续执行，
            为False时，会执行该用例所有断言
        """
        if is_raise:
            super().assertTrue(expr, msg)
        else:
            try:
                super().assertTrue(expr, msg)
            except BaseException as e:
                a, b, exc_tb = sys.exc_info()
                frame = exc_tb.tb_frame.f_back
                frame_info = inspect.getframeinfo(frame)
                code = frame_info.code_context[0].strip()
                f_back_frame = inspect.currentframe().f_back
                co_filename = os.path.basename(f_back_frame.f_code.co_filename)
                co_name = f_back_frame.f_code.co_name
                lineno = f_back_frame.f_lineno
                self.verificationErrors.append(
                    f'{"-" * 80}\n【断言错误】:\n路径: {co_filename} - line:【{lineno}】- {co_name}\n代码: {code}\n错误: {str(e)}')

    def assertFalse(self, expr, msg=None, is_raise=True):
        if is_raise:
            super().assertFalse(expr, msg)
        else:
            try:
                super().assertFalse(expr, msg)
            except BaseException as e:
                a, b, exc_tb = sys.exc_info()
                frame = exc_tb.tb_frame.f_back
                frame_info = inspect.getframeinfo(frame)
                code = frame_info.code_context[0].strip()
                f_back_frame = inspect.currentframe().f_back
                co_filename = os.path.basename(f_back_frame.f_code.co_filename)
                co_name = f_back_frame.f_code.co_name
                lineno = f_back_frame.f_lineno
                self.verificationErrors.append(
                    f'{"-" * 80}\n【断言错误】:\n路径: {co_filename} - line:【{lineno}】- {co_name}\n代码: {code}\n错误: {str(e)}')

    def assertEqual(self, first, second, msg=None, is_raise=True):
        if is_raise:
            super().assertEqual(first, second, msg)
        else:
            try:
                super().assertEqual(first, second, msg)
            except BaseException as e:
                a, b, exc_tb = sys.exc_info()
                frame = exc_tb.tb_frame.f_back
                frame_info = inspect.getframeinfo(frame)
                code = frame_info.code_context[0].strip()
                f_back_frame = inspect.currentframe().f_back
                co_filename = os.path.basename(f_back_frame.f_code.co_filename)
                co_name = f_back_frame.f_code.co_name
                lineno = f_back_frame.f_lineno
                self.verificationErrors.append(
                    f'{"-" * 80}\n【断言错误】:\n路径: {co_filename} - line:【{lineno}】- {co_name}\n代码: {code}\n错误: {str(e)}')

    def assertNotEqual(self, first, second, msg=None, is_raise=True):
        if is_raise:
            super().assertNotEqual(first, second, msg)
        else:
            try:
                super().assertNotEqual(first, second, msg)
            except BaseException as e:
                a, b, exc_tb = sys.exc_info()
                frame = exc_tb.tb_frame.f_back
                frame_info = inspect.getframeinfo(frame)
                code = frame_info.code_context[0].strip()
                f_back_frame = inspect.currentframe().f_back
                co_filename = os.path.basename(f_back_frame.f_code.co_filename)
                co_name = f_back_frame.f_code.co_name
                lineno = f_back_frame.f_lineno
                self.verificationErrors.append(
                    f'{"-" * 80}\n【断言错误】:\n路径: {co_filename} - line:【{lineno}】- {co_name}\n代码: {code}\n错误: {str(e)}')

    def assertIsNone(self, expr, msg=None, is_raise=True):
        if is_raise:
            super().assertIsNone(expr, msg)
        else:
            try:
                super().assertIsNone(expr, msg)
            except BaseException as e:
                a, b, exc_tb = sys.exc_info()
                frame = exc_tb.tb_frame.f_back
                frame_info = inspect.getframeinfo(frame)
                code = frame_info.code_context[0].strip()
                f_back_frame = inspect.currentframe().f_back
                co_filename = os.path.basename(f_back_frame.f_code.co_filename)
                co_name = f_back_frame.f_code.co_name
                lineno = f_back_frame.f_lineno
                self.verificationErrors.append(
                    f'{"-" * 80}\n【断言错误】:\n路径: {co_filename} - line:【{lineno}】- {co_name}\n代码: {code}\n错误: {str(e)}')

    def assertIsNotNone(self, expr, msg=None, is_raise=True):
        if is_raise:
            super().assertIsNotNone(expr, msg)
        else:
            try:
                super().assertIsNotNone(expr, msg)
            except BaseException as e:
                a, b, exc_tb = sys.exc_info()
                frame = exc_tb.tb_frame.f_back
                frame_info = inspect.getframeinfo(frame)
                code = frame_info.code_context[0].strip()
                f_back_frame = inspect.currentframe().f_back
                co_filename = os.path.basename(f_back_frame.f_code.co_filename)
                co_name = f_back_frame.f_code.co_name
                lineno = f_back_frame.f_lineno
                self.verificationErrors.append(
                    f'{"-" * 80}\n【断言错误】:\n路径: {co_filename} - line:【{lineno}】- {co_name}\n代码: {code}\n错误: {str(e)}')

    def assertIn(self, member, container, msg=None, is_raise=True):
        if is_raise:
            super().assertIn(member, container, msg)
        else:
            try:
                super().assertIn(member, container, msg)
            except BaseException as e:
                a, b, exc_tb = sys.exc_info()
                frame = exc_tb.tb_frame.f_back
                frame_info = inspect.getframeinfo(frame)
                code = frame_info.code_context[0].strip()
                f_back_frame = inspect.currentframe().f_back
                co_filename = os.path.basename(f_back_frame.f_code.co_filename)
                co_name = f_back_frame.f_code.co_name
                lineno = f_back_frame.f_lineno
                self.verificationErrors.append(
                    f'{"-" * 80}\n【断言错误】:\n路径: {co_filename} - line:【{lineno}】- {co_name}\n代码: {code}\n错误: {str(e)}')

    def assertNotIn(self, member, container, msg=None, is_raise=True):
        if is_raise:
            super().assertNotIn(member, container, msg)
        else:
            try:
                super().assertNotIn(member, container, msg)
            except BaseException as e:
                a, b, exc_tb = sys.exc_info()
                frame = exc_tb.tb_frame.f_back
                frame_info = inspect.getframeinfo(frame)
                code = frame_info.code_context[0].strip()
                f_back_frame = inspect.currentframe().f_back
                co_filename = os.path.basename(f_back_frame.f_code.co_filename)
                co_name = f_back_frame.f_code.co_name
                lineno = f_back_frame.f_lineno
                self.verificationErrors.append(
                    f'{"-" * 80}\n【断言错误】:\n路径: {co_filename} - line:【{lineno}】- {co_name}\n代码: {code}\n错误: {str(e)}')

    def assertLess(self, a, b, msg=None, is_raise=True):
        if is_raise:
            super().assertLess(a, b, msg)
        else:
            try:
                super().assertLess(a, b, msg)
            except BaseException as e:
                a, b, exc_tb = sys.exc_info()
                frame = exc_tb.tb_frame.f_back
                frame_info = inspect.getframeinfo(frame)
                code = frame_info.code_context[0].strip()
                f_back_frame = inspect.currentframe().f_back
                co_filename = os.path.basename(f_back_frame.f_code.co_filename)
                co_name = f_back_frame.f_code.co_name
                lineno = f_back_frame.f_lineno
                self.verificationErrors.append(
                    f'{"-" * 80}\n【断言错误】:\n路径: {co_filename} - line:【{lineno}】- {co_name}\n代码: {code}\n错误: {str(e)}')

    def assertLessEqual(self, a, b, msg=None, is_raise=True):
        if is_raise:
            super().assertLessEqual(a, b, msg)
        else:
            try:
                super().assertLessEqual(a, b, msg)
            except BaseException as e:
                a, b, exc_tb = sys.exc_info()
                frame = exc_tb.tb_frame.f_back
                frame_info = inspect.getframeinfo(frame)
                code = frame_info.code_context[0].strip()
                f_back_frame = inspect.currentframe().f_back
                co_filename = os.path.basename(f_back_frame.f_code.co_filename)
                co_name = f_back_frame.f_code.co_name
                lineno = f_back_frame.f_lineno
                self.verificationErrors.append(
                    f'{"-" * 80}\n【断言错误】:\n路径: {co_filename} - line:【{lineno}】- {co_name}\n代码: {code}\n错误: {str(e)}')

    def assertGreater(self, a, b, msg=None, is_raise=True):
        if is_raise:
            super().assertGreater(a, b, msg)
        else:
            try:
                super().assertGreater(a, b, msg)
            except BaseException as e:
                a, b, exc_tb = sys.exc_info()
                frame = exc_tb.tb_frame.f_back
                frame_info = inspect.getframeinfo(frame)
                code = frame_info.code_context[0].strip()
                f_back_frame = inspect.currentframe().f_back
                co_filename = os.path.basename(f_back_frame.f_code.co_filename)
                co_name = f_back_frame.f_code.co_name
                lineno = f_back_frame.f_lineno
                self.verificationErrors.append(
                    f'{"-" * 80}\n【断言错误】:\n路径: {co_filename} - line:【{lineno}】- {co_name}\n代码: {code}\n错误: {str(e)}')

    def assertGreaterEqual(self, a, b, msg=None, is_raise=True):
        if is_raise:
            super().assertGreaterEqual(a, b, msg)
        else:
            try:
                super().assertGreaterEqual(a, b, msg)
            except BaseException as e:
                a, b, exc_tb = sys.exc_info()
                frame = exc_tb.tb_frame.f_back
                frame_info = inspect.getframeinfo(frame)
                code = frame_info.code_context[0].strip()
                f_back_frame = inspect.currentframe().f_back
                co_filename = os.path.basename(f_back_frame.f_code.co_filename)
                co_name = f_back_frame.f_code.co_name
                lineno = f_back_frame.f_lineno
                self.verificationErrors.append(
                    f'{"-" * 80}\n【断言错误】:\n路径: {co_filename} - line:【{lineno}】- {co_name}\n代码: {code}\n错误: {str(e)}')

    def _callTestMethod(self, method):
        if method() is not None:
            warnings.warn(f'It is deprecated to return a value that is not None from a '
                          f'test case ({method})', DeprecationWarning,
                          stacklevel=2)  # 2025.4.1 level=3->2,否则一些用例失败的定位不会显示到报告.

    def run(self, result=None):
        if result is None:
            result = self.defaultTestResult()
            startTestRun = getattr(result, 'startTestRun', None)
            stopTestRun = getattr(result, 'stopTestRun', None)
            if startTestRun is not None:
                startTestRun()
        else:
            stopTestRun = None

        ret = []
        result.startTest(self)
        try:
            testMethod = getattr(self, self._testMethodName)
            if (getattr(self.__class__, "__unittest_skip__", False) or
                    getattr(testMethod, "__unittest_skip__", False)):
                # If the class or method was skipped.
                skip_why = (getattr(self.__class__, '__unittest_skip_why__', '')
                            or getattr(testMethod, '__unittest_skip_why__', ''))
                _addSkip(result, self, skip_why)
                return result

            expecting_failure = (
                    getattr(self, "__unittest_expecting_failure__", False) or
                    getattr(testMethod, "__unittest_expecting_failure__", False)
            )
            outcome = _Outcome(result)
            start_time = time.perf_counter()
            try:
                self._outcome = outcome

                with outcome.testPartExecutor(self):
                    if (getattr(self.__class__, "__unittest_fail__", False) or
                            getattr(testMethod, "__unittest_fail__", False)):
                        # print('Failed by dependon_fail directly!. do not setup for saving time')
                        pass
                    else:
                        try:
                            self.get_first_process_dict()
                        except:
                            pass
                        aklog_info('~~~~~~~~~~~~~~~~~~~~~~~~ setup ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
                        self.verificationErrors = []
                        self._callSetUp()

                if param_get_reboot_process_flag():
                    # setup之后做进程ID更新和判断: 为上一条teardownclass, 本次setupclass主动重启服务.
                    try:
                        ret = self.check_process_state()
                    except:
                        ret = ['进程检查出现异常', traceback.format_exc()]
                    if ret != []:
                        write_to_html_report(
                            title='终端进程检查',
                            case_name=f'【{self.__class__.__name__}】 -- 【{self._testMethodName}】',
                            process_info=ret
                        )

                # 在def test之前恢复重启的标志位.
                param_put_reboot_process_flag(False)
                if outcome.success:
                    outcome.expecting_failure = expecting_failure
                    with outcome.testPartExecutor(self):
                        if (getattr(self.__class__, "__unittest_fail__", False) or getattr(testMethod,
                                                                                           "__unittest_fail__", False)):
                            self.assertFalse(True, msg=testMethod.__unittest_fail_why__)
                        else:
                            aklog_info('~~~~~~~~~~~~~~~~~~~~~~~ start test ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
                            self._callTestMethod(testMethod)
                            if self.verificationErrors:  # assert raise
                                errors = '\n' + '\n'.join([str(i) for i in self.verificationErrors])
                                self.verificationErrors = []
                                raise RuntimeError(errors)

                    outcome.expecting_failure = False
                    with outcome.testPartExecutor(self):
                        # 2025.3.31 lex: 增加faildump. teardown 在 with outcome.testPartExecutor(self)后再执行
                        # self._callTearDown()
                        pass

                    ifskip = False
                    if getattr(result, 'skipped', []) and result.skipped[-1][0]._testMethodName == self._testMethodName:
                        ifskip = True
                    if not outcome.success:
                        if (getattr(self.__class__, "__unittest_fail__", False) or getattr(testMethod,
                                                                                           "__unittest_fail__", False)):
                            # print('Failed by dependon_fail directly!. do not fail dump for saving time')
                            pass
                        else:
                            if not ifskip:
                                # self.skipTest的不去导出日志.
                                aklog_info('~~~~~~~~~~~~~~~~~~~~~~~ fail dump ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
                                self.faildump()

                    # teardown结束前做一次进程状态判断.
                    try:
                        ret = self.check_process_state()
                    except:
                        ret = ['进程检查出现异常', traceback.format_exc()]
                    if ret != []:
                        write_to_html_report(
                            title='终端进程检查',
                            case_name=f'【{self.__class__.__name__}】 -- 【{self._testMethodName}】',
                            process_info=ret
                        )
                        self.export_log_when_check_process_failed()
                    try:
                        aklog_info('~~~~~~~~~~~~~~~~~~~~~~~ tear down ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
                        self._callTearDown()
                    except:
                        aklog_error('~~~~~~~~~~~~~~~~~~~~~~~ tear down error~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
                        aklog_debug(traceback.format_exc())

                    # teardown结束后做一次复位标志
                    param_put_reboot_process_flag(False)
                self.doCleanups()
                self._addDuration(result, (time.perf_counter() - start_time))
                if outcome.success:
                    if expecting_failure:
                        if outcome.expectedFailure:
                            self._addExpectedFailure(result, outcome.expectedFailure)
                        else:
                            self._addUnexpectedSuccess(result)
                    else:
                        result.addSuccess(self)
                return result

            finally:
                # explicitly break reference cycle:
                # outcome.expectedFailure -> frame -> outcome -> outcome.expectedFailure
                outcome.expectedFailure = None
                outcome = None

                # clear the outcome, no more needed
                self._outcome = None

        finally:
            if ret and result.error_text:
                try:
                    result.error_text[1].args = (
                        result.error_text[1].args[0] + '\n' + '*' * 80 + '\n' + '\n'.join(ret),)
                except:
                    pass
            result.stopTest(self)
            if stopTestRun is not None:
                stopTestRun()

    def faildump(self):
        pass

    def check_process_state(self):
        """
        返回 [] 代表正常.
        否则返回的是错误的进程信息数组
        """
        return []

    def get_first_process_dict(self):
        return {}

    def export_log_when_check_process_failed(self):
        pass


class AK_linuxindoor(AK_unittest_screenshot):
    master_linux_indoor = None
    slave_linux_door = None

    def faildump(self):
        if self.master_linux_indoor:
            self.master_linux_indoor.screen_shot()
            self.master_linux_indoor.export_syslog_to_results_dir(self.module_name)

    def check_process_state(self):
        """
        返回 [] 代表正常.
        否则返回的是错误的进程信息数组
        """
        if self.master_linux_indoor:
            ret = self.master_linux_indoor.intercom_check_process_state()
            return ret
        return []

    def get_first_process_dict(self):
        if self.master_linux_indoor:
            ret = self.master_linux_indoor.intercom_get_first_process_dict()
            return ret

    def export_log_when_check_process_failed(self):
        if self.master_linux_indoor:
            self.master_linux_indoor.export_syslog_to_results_dir(self.module_name)


class AK_unittest_linuxindoor(AK_linuxindoor):
    pass


class AK_androidindoor(AK_unittest_screenshot):
    master_android_indoor = None
    slave_linux_door = None

    def faildump(self):
        if self.master_android_indoor:
            self.master_android_indoor.app.screen_shot()
            self.master_android_indoor.browser.screen_shot()
            self.master_android_indoor.browser.export_syslog_to_results_dir(self.module_name)

    def check_process_state(self):
        """
        返回 [] 代表正常.
        否则返回的是错误的进程信息数组
        """
        if self.master_android_indoor:
            ret = self.master_android_indoor.browser.intercom_check_process_state()
            return ret
        return []

    def get_first_process_dict(self):
        if self.master_android_indoor:
            ret = self.master_android_indoor.browser.intercom_get_first_process_dict()
            return ret

    def export_log_when_check_process_failed(self):
        if self.master_android_indoor:
            self.master_android_indoor.browser.export_syslog_to_results_dir(self.module_name)


class AK_unittest_androidindoor(AK_androidindoor):
    pass


class AK_linuxdoor(AK_unittest_screenshot):
    master_linux_door = None
    slave_linux_indoor = None
    module_name = None
    img = []

    @classmethod
    def tearDownClass(cls):
        aklog_info('~~~~~~~~~~~~~~~~~~~~~~~ tear down class ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
        # cls.master_linux_door.hang_up_call()
        cls.master_linux_door.browser_close_and_quit()
        if cls.slave_linux_indoor:
            cls.slave_linux_indoor.browser_close_and_quit()

    def setUp(self):
        aklog_info("%s, %s" % (self.__class__.__name__, self._testMethodName))
        self.imgs = []
        if self.master_linux_door:
            self.master_linux_door.hang_up_call()
        if self.slave_linux_indoor:
            self.slave_linux_indoor.hang_up_call()
            # 2025.7.4 lex: 临时添加, 作为门口机配合机的时候一直关闭dnd
            if self.slave_linux_indoor.get_input_value_by_id(self.slave_linux_indoor.ui_element_info['dnd']) in [
                'DND On', 'DND ON']:
                self.slave_linux_indoor.click_btn_and_refresh_by_id(self.slave_linux_indoor.ui_element_info['dnd'])
                self.slave_linux_indoor.click_btn_and_refresh_by_id('7175')

    def tearDown(self):
        if self.master_linux_door:
            self.master_linux_door.hang_up_call()
        if self.slave_linux_indoor:
            self.slave_linux_indoor.hang_up_call()
            self.slave_linux_indoor.return_home()

    def faildump(self):
        if self.master_linux_door:
            self.master_linux_door.screen_shot()
        if self.slave_linux_indoor:
            self.slave_linux_indoor.screen_shot()
        if self.master_linux_door:
            self.master_linux_door.export_syslog_to_results_dir(self.module_name)

            # temp  2025.8.8
            log_time = time.strftime('%H%M%S', time.localtime(time.time()))
            log_dir = '{}\\{}'.format(aklog_get_result_dir(), 'device_log')
            log_file = '{}\\config--{}--{}--{}.tgz'.format(log_dir, self.module_name, 'master_linux_door', log_time)
            os.makedirs(log_file, exist_ok=True)
            export_system_log_file = self.master_linux_door.device_config.get_chrome_download_dir() + 'config.tgz'
            self.master_linux_door.web_export_config()
            if os.path.exists(export_system_log_file):
                import shutil
                aklog_info(f'copy {export_system_log_file} --> {log_file}')
                shutil.copy2(export_system_log_file, log_file)

    def export_log_when_check_process_failed(self):
        if self.master_linux_door:
            self.master_linux_door.export_syslog_to_results_dir(self.module_name)
            # temp  2025.8.8
            log_time = time.strftime('%H%M%S', time.localtime(time.time()))
            log_dir = '{}\\{}'.format(aklog_get_result_dir(), 'device_log')
            log_file = '{}\\config--{}--{}--{}.tgz'.format(log_dir, self.module_name, 'master_linux_door', log_time)
            os.makedirs(log_file, exist_ok=True)
            export_system_log_file = self.master_linux_door.device_config.get_chrome_download_dir() + 'config.tgz'
            self.master_linux_door.web_export_config()
            if os.path.exists(export_system_log_file):
                import shutil
                aklog_info(f'copy {export_system_log_file} --> {log_file}')
                shutil.copy2(export_system_log_file, log_file)

    def check_process_state(self):
        """
        返回 [] 代表正常.
        否则返回的是错误的进程信息数组
        """
        if self.master_linux_door:
            ret = self.master_linux_door.intercom_check_process_state()
            return ret
        return []

    def get_first_process_dict(self):
        if self.master_linux_door:
            ret = self.master_linux_door.intercom_get_first_process_dict()
            return ret


class AKunittest_linuxdoor(AK_linuxdoor):
    pass


class AK_Androiddoor(AK_unittest_screenshot):
    master_android_door = None
    slave_linux_indoor = None
    module_name = None

    @classmethod
    def tearDownClass(cls):
        aklog_info('~~~~~~~~~~~~~~~~~~~~~~~ tear down class ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
        cls.master_android_door.browser.browser_close_and_quit()
        if cls.slave_linux_indoor:
            cls.slave_linux_indoor.browser_close_and_quit()

    def setUp(self):
        if self.master_android_door:
            self.master_android_door.app.reset_imgs()
            self.imgs = []
            self.master_android_door.return_home_page()
        if hasattr(self, 'slave_linux_indoor') and self.slave_linux_indoor:
            self.slave_linux_indoor.return_home()
            if self.slave_linux_indoor.get_input_value_by_id(self.slave_linux_indoor.ui_element_info['dnd']) in [
                'DND On', 'DND ON']:
                self.slave_linux_indoor.click_btn_and_refresh_by_id(self.slave_linux_indoor.ui_element_info['dnd'])
                self.slave_linux_indoor.click_btn_and_refresh_by_id('7175')

    def tearDown(self):
        if self.master_android_door:
            self.imgs.extend(self.master_android_door.app.get_imgs())
            self.master_android_door.api_hangup()
            self.master_android_door.hang_up_call()
        if hasattr(self, 'slave_linux_indoor') and self.slave_linux_indoor:
            self.slave_linux_indoor.hang_up_call()
            self.slave_linux_indoor.return_home()

    def faildump(self):
        if self.master_android_door:
            self.master_android_door.app.screen_shot()
            self.master_android_door.browser.screen_shot()
            self.master_android_door.browser.export_syslog_to_results_dir(self.module_name)

    def export_log_when_check_process_failed(self):
        if self.master_android_door:
            self.master_android_door.browser.export_syslog_to_results_dir(self.module_name)

    def check_process_state(self):
        """
        返回 [] 代表正常.
        否则返回的是错误的进程信息数组
        """
        if self.master_android_door:
            ret = self.master_android_door.browser.intercom_check_process_state()
            return ret
        return []

    def get_first_process_dict(self):
        if self.master_android_door:
            ret = self.master_android_door.browser.intercom_get_first_process_dict()
            return ret


class AKunittest_androiddoor(AK_Androiddoor):
    """多一层, 修复安卓door工程def setup里super的问题."""
    pass


class AK_accessdoor(AK_unittest_screenshot):
    master_access_door = None
    slave_linux_indoor = None

    def setUp(self):
        self.imgs = []
        if self.master_access_door:
            self.master_access_door.return_home_page()
        if self.slave_linux_indoor:
            self.slave_linux_indoor.enter_home()

    def tearDown(self):
        if self.master_access_door:
            self.master_access_door.hang_up_call()
        if self.slave_linux_indoor:
            self.slave_linux_indoor.hang_up_call()
            if self.slave_linux_indoor.get_input_value_by_id(self.slave_linux_indoor.ui_element_info['dnd']) in [
                'DND On', 'DND ON']:
                self.slave_linux_indoor.click_btn_and_refresh_by_id(self.slave_linux_indoor.ui_element_info['dnd'])
                self.slave_linux_indoor.click_btn_and_refresh_by_id('7175')

    def faildump(self):
        if self.master_access_door:
            self.master_access_door.screen_shot()
            self.master_access_door.export_syslog_to_results_dir(self.module_name)

    def export_log_when_check_process_failed(self):
        if self.master_access_door:
            self.master_access_door.export_syslog_to_results_dir(self.module_name)

    def check_process_state(self):
        """
        返回 [] 代表正常.
        否则返回的是错误的进程信息数组
        """
        if self.master_access_door:
            ret = self.master_access_door.intercom_check_process_state()
            return ret
        return []

    def get_first_process_dict(self):
        if self.master_access_door:
            ret = self.master_access_door.intercom_get_first_process_dict()
            return ret


class AK_unittest_accessdoor(AK_accessdoor):
    pass


class AK_accesscontrol(AK_unittest_screenshot):
    master_access_control = None

    def setUp(self):
        self.imgs = []
        if self.master_access_control:
            self.master_access_control.start_test()

    def tearDown(self):
        pass

    def faildump(self):
        if self.master_access_control:
            self.master_access_control.web.screen_shot()
            self.master_access_control.web.export_syslog_to_results_dir(self.module_name)

    def export_log_when_check_process_failed(self):
        if self.master_access_control:
            self.master_access_control.web.export_syslog_to_results_dir(self.module_name)

    def check_process_state(self):
        """
        返回 [] 代表正常.
        否则返回的是错误的进程信息数组
        """
        if self.master_access_control:
            ret = self.master_access_control.web.intercom_check_process_state()
            return ret
        return []

    def get_first_process_dict(self):
        if self.master_access_control:
            ret = self.master_access_control.web.intercom_get_first_process_dict()
            return ret


class AK_unittest_accesscontrol(AK_accesscontrol):
    pass


def robot_info_msg(msg_content, receiverslist=None):
    """
    2024.7.11 lex 30天压测接口, 不根据weixin-state, 直接发送机器人信息.
    """
    if not receiverslist:
        email_receivers = param_get_email_receivers()
    else:
        if type(receiverslist) == list:
            email_receivers = receiverslist
        else:
            email_receivers = [receiverslist]
    robot_send_text_msg(msg_content, *email_receivers)


def unittest_get_all_classes_from_module(module):
    """获取模块中的所有类，包括 import * 导入的类"""
    class_list = []
    if hasattr(module, '__all__'):
        symbols = module.__all__
    else:
        symbols = dir(module)

    for symbol in symbols:
        obj = getattr(module, symbol)
        if inspect.isclass(obj) and obj.__module__.startswith(module.__name__) and obj not in class_list:
            class_list.append(obj)
    return class_list


def unittest_get_abstract_class_list(package):
    """递归获取包中的所有类"""
    class_list = []
    if not hasattr(package, '__path__'):
        return class_list
    for _, module_name, is_pkg in pkgutil.walk_packages(package.__path__, package.__name__ + '.'):
        module = importlib.import_module(module_name)
        _list = unittest_get_all_classes_from_module(module)
        for module in _list:
            if module not in class_list:
                class_list.append(module)
        if is_pkg:
            _list = unittest_get_abstract_class_list(module)
            for module in _list:
                if module not in class_list:
                    class_list.append(module)
    return class_list


def unittest_generate_base_abstract_list(abstract_package, base_package, series_name=None, common_series_name=None):
    """生成要检查的列表"""
    base_abstract_list = []
    abstract_class_list = unittest_get_abstract_class_list(abstract_package)
    print(abstract_class_list)
    for tclass in abstract_class_list:
        if tclass.__name__.startswith('AbstractCommonFlowBase') or tclass.__name__.startswith('AbstractBase'):
            continue
        base_class_name = tclass.__name__.replace('Abstract', '')
        if series_name and common_series_name:
            base_class_name = base_class_name.replace(common_series_name, series_name)
        try:
            base_class = getattr(base_package, base_class_name)
        except AttributeError:
            continue
        base_abstract = [base_class, tclass]
        base_abstract_list.append(base_abstract)
    return base_abstract_list


class UnittestTestDeviceImplementations(unittest.TestCase):
    """
    定义接口抽象类单元测试
    可以检查抽象类定义的接口是否都被各机型的base基类重写了，以此来保证各机型的base基类都包含用抽象类定义的接口方法
    定义的参数
    """

    def check_methods(self, subclass, abstract_class, exclude_methods=None):
        if exclude_methods is None:
            exclude_methods = []

        abstract_methods = set(getattr(abstract_class, '__abstractmethods__', None))
        if not abstract_methods:
            abstract_methods = set()
        subclass_dict = getattr(subclass, '__class__').__dict__
        subclass_name = getattr(subclass, '__class__').__name__
        sub_methods = {name for name, value in subclass_dict.items() if callable(value)}

        # Exclude methods that are unique to the subclass
        sub_methods -= set(exclude_methods)
        missing_methods = abstract_methods - sub_methods

        self.assertEqual(len(missing_methods), 0,
                         f"The following methods are not implemented in {subclass_name}: {missing_methods}")

        # Check method signatures
        for method in abstract_methods:
            if method in exclude_methods:
                continue
            abstract_method = getattr(abstract_class, method)
            subclass_method = getattr(subclass.__class__, method)
            self.check_method_signature(subclass_method, abstract_method, subclass_name, method)

    def check_method_signature(self, subclass_method, abstract_method, subclass_name, method_name):
        abstract_signature = inspect.signature(abstract_method)
        subclass_signature = inspect.signature(subclass_method)

        # Extract parameter names and kinds, ignoring default values
        abstract_params = [(name, param.kind) for name, param in abstract_signature.parameters.items()]
        subclass_params = [(name, param.kind) for name, param in subclass_signature.parameters.items()]

        self.assertEqual(abstract_params, subclass_params,
                         f"The method '{method_name}' in {subclass_name} does not match the signature of the abstract method.\n"
                         f"Expected: {abstract_params}\n"
                         f"Found: {subclass_params}")
