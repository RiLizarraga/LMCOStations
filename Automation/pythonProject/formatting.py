
from colorama import Fore, Style, init

init() # Call this once at the start of your script

print(f"{Fore.GREEN}This text is green.{Style.RESET_ALL}")
print(f"{Fore.RED}{Style.BRIGHT}This is bold red.{Style.RESET_ALL}")
#############################################
pauseHere = input("...press ENTER")
from rich.console import Console
from rich.table import Table

console = Console()

table = Table(title="Star Wars Movies")

table.add_column("Released", style="cyan", no_wrap=True)
table.add_column("Title", style="magenta")
table.add_column("Box Office", justify="right", style="green")

table.add_row("Dec 20, 2019", "Star Wars: The Rise of Skywalker", "$1,074,144,302")
table.add_row("Dec 15, 2017", "Star Wars: The Last Jedi", "$1,332,159,362")
table.add_row("Dec 16, 2016", "Rogue One: A Star Wars Story", "$1,056,057,273")
table.add_row("Dec 18, 2015", "Star Wars: The Force Awakens", "$2,068,223,624")

console.print(table)

#############################################
pauseHere = input("...press ENTER")

from tabulate import tabulate
data = [
    ["Alice", 30, "New York"],
    ["Bob", 24, "London"],
    ["Charlie", 35, "Paris"]
]
headers = ["Name", "Age", "City"]

print(tabulate(data, headers=headers, tablefmt="grid"))
# You can change "grid" to "fancy_grid", "pipe", "simple", etc.

#############################################
pauseHere = input("...press ENTER")
from prettytable import PrettyTable

my_table = PrettyTable()
my_table.field_names = ["City", "Area", "Population"]
my_table.add_row(["New York", 789, 8419000])
my_table.add_row(["Los Angeles", 469, 3990000])
my_table.add_row(["Chicago", 234, 2716000])

print(my_table)