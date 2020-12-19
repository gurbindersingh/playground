def get_project_root():
    project_root = __file__.split("utils")[0]
    return project_root


if __name__ == "__main__":
    print(get_project_root())
