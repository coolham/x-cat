import os
import shutil

def clean_temp_files(directory: str) -> None:
    """
    清理项目目录中的临时文件和日志文件

    Args:
        directory: 项目根目录
    """
    temp_file_extensions = ['.pyc', '.pyo', '.log', '.tmp']
    temp_dirs = ['__pycache__', 'logs', 'temp']

    for root, dirs, files in os.walk(directory):
        # 删除临时文件
        for file in files:
            if any(file.endswith(ext) for ext in temp_file_extensions):
                file_path = os.path.join(root, file)
                try:
                    os.remove(file_path)
                    print(f"已删除文件: {file_path}")
                except Exception as e:
                    print(f"无法删除文件 {file_path}: {e}")

        # 删除临时目录
        for dir_name in dirs:
            if dir_name in temp_dirs:
                dir_path = os.path.join(root, dir_name)
                try:
                    shutil.rmtree(dir_path)
                    print(f"已删除目录: {dir_path}")
                except Exception as e:
                    print(f"无法删除目录 {dir_path}: {e}")

if __name__ == "__main__":
    project_dir = os.path.dirname(os.path.abspath(__file__))
    clean_temp_files(project_dir)
    print("清理完成！")