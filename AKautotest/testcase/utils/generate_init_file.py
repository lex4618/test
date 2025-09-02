"""
@Version: 1.0
@Author: jason
@Data: 2024/1/5
@Comment: 用于生成Base目录下的__init__.py文件，将Base目录下的各个模块导入到__init__.py
可以将该文件复制到Base目录下执行，也可以复制Base目录路径赋值给base_dir
"""

import os


def generate_base_init_file(base_dir=None):
    """生成Base模块下的__init__.py文件"""
    content = ""
    content += "import sys\n"
    content += "import os\n\n"
    content += "# 将base模块目录添加到sys.path，base模块就可以使用绝对路径导入，但__init__仍可以使用相对路径导入\n"
    content += "sys.path.append(os.path.dirname(__file__))\n\n"

    if not base_dir:
        base_dir = os.path.dirname(__file__)
    if 'Base' not in base_dir:
        print('当前路径 %s 不是Base目录' % base_dir)
        return

    module_list = []
    for x in os.listdir(base_dir):
        file_name, ext = os.path.splitext(x)
        class_name = file_name[3:]  # 默认base模块的类名跟文件名只相差lib开口，如果类名有修改，则要检查
        if ext != ".py" or not file_name.startswith("lib"):  # extension扩展名包含点
            continue
        import_str = "from .%s import %s\n" % (file_name, class_name)
        content += import_str
        module_list.append(class_name)

    content += "\n# 模块导入完成后，即可把该目录从sys.path移除，不影响后续base模块导入\n"
    content += "sys.path.remove(os.path.dirname(__file__))\n\n"
    content += "__all__ = [\n"
    for class_name in module_list:
        content += '    "%s",\n' % class_name

    content = content[0:-2] + '\n]\n'

    init_file = os.path.join(base_dir, "__init__.py")
    with open(init_file, "w", encoding='utf-8') as fw:
        fw.write(content)


if __name__ == '__main__':
    base_dir = r'E:\SVN_Python\Develop\AKautotest\testcase\module\AndroidIndoor\UI4_1\Base'
    generate_base_init_file(base_dir)
