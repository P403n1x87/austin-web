from psutil import cpu_percent


def main():
    for i in range(10):
        cpu_percent(interval=1, percpu=True)


if __name__ == "__main__":
    main()
