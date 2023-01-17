import pyomo.environ as pyo
import pandas as pd
from pathlib import Path
import preprocess_data as dat

class pyomo_model:
    def __init__(self, data_path: Path, year: int):
        self.data_path = data_path
        self.year = year
        self.adj_list = dat.create_adj_list(data_path)
        self.adj_matrix = dat.gen_adj_matrix(self.adj_list)
        self.df_init, self.counties = dat.data_ingest(data_path, year)
        self.df = dat.create_df(self.df_init, self.counties, self.adj_list)
        self.model = pyo.AbstractModel()
    
    def param_adj(self, m, i, j):
        return int(j in self.adj_matrix[i])
    
    def param_pop(self, m, i):
        return self.df["population"][i - 1]
    
    def con_a(self, m, i):
        return sum((m.a[i, j] * m.x[j]) for j in m.J) >= m.y[i]
    
    def con_x(self, m):
        return sum(m.x[j] for j in m.J) <= m.k
    
    def obj_sum(self, m):
        return pyo.summation(m.p, m.y)
    
    def define_model(self):
        # value of n (number of counties)
        self.model.n = pyo.Param(initialize=88)

        # range of i and j (iterating over counties)
        self.model.I = pyo.RangeSet(1, self.model.n)
        self.model.J = pyo.RangeSet(1, self.model.n)

        # TOSET limit on number of pirincipal places of buisnesses opened (init to 5)
        self.model.k = pyo.Var(within=pyo.NonNegativeIntegers, initialize=5)

        self.model.p = pyo.Param(self.model.I, initialize=self.param_pop)  # population of county i

        # self.model.a = pyo.Set(self.model.I, self.model.J, within=pyo.Binary, initialize=self.param_adj)  # 1 if county i and j are adjacent
        self.model.a = pyo.Var(self.model.I, self.model.J, domain=pyo.Binary, initialize=self.param_adj)  # 1 if county i and j are adjacent

        self.model.x = pyo.Var(self.model.J, domain=pyo.Binary)  # 1 if principal place of business is opened in county j
        self.model.y = pyo.Var(self.model.I, domain=pyo.Binary)  # 1 if county i is covered

        self.model.obj = pyo.Objective(rule=self.obj_sum, sense=pyo.maximize)

        self.model.a_constraint = pyo.Constraint(self.model.I, rule=self.con_a)
        self.model.x_constraint = pyo.Constraint(rule=self.con_x)

    def create_instance(self):
        return self.model.create_instance()
    
    def solve(self):
        opt = pyo.SolverFactory("cbc")
        results = opt.solve(self.instance).write()
        # self.instance.pprint()
        # self.instance.solutions.store_to(results)
        return results
        
    def print_data(self):
        # print(self.df.head())
        print (self.instance.y.display())

if __name__ == "__main__":
    model21 = pyomo_model(Path("data"), 2021)
    
    model21.define_model()
    model21.instance = model21.create_instance()
    results = model21.solve()
    model21.print_data()
    # model21.pprint()
    # model21.x.get_values()
    # solution.print_data()
    # solution.solutions.store_to(results)


# def param_adj(m, i, j):
#     return int(j in adj_matrix[i])

# def param_pop(m, i):
#     return df["population"][i - 1]

# def con_a(m, i):
#     return sum((m.a[i, j] * m.x[j]) for j in m.J) >= m.y[i]

# def con_x(m):
#     return sum(m.x[j] for j in m.J) <= m.k

# def obj_sum(m):
#     return pyo.summation(m.p, m.y)