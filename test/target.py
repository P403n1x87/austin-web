#!/usr/bin/env python3

from psutil import cpu_percent


def main():
    for _ in range(20):
        cpu_percent(interval=0.2, percpu=True)


if __name__ == "__main__":
    main()
