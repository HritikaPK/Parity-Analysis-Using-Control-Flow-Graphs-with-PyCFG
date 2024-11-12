from pycfg.pycfg import PyCFG, CFGNode, slurp
import argparse
import re
# import ast

var_value_env ={} # store values of all variables
parity_env = {}  # initialize empty parity environment

# Parity states
BOTTOM, EVEN, ODD, TOP = "Bottom", "Even", "Odd", "Top"

# Function for parity lattice meet operation for merging values
def meet(a, b):
    if a == b:
        return a
    elif a == BOTTOM:
        return b
    elif b == BOTTOM:
        return a
    else:
        return TOP

# # Function for parity addition operation
def add_parity(a, b):
    if a == BOTTOM or b == BOTTOM:
        return BOTTOM
    elif a == EVEN and b == EVEN:
        return EVEN
    elif a == ODD and b == ODD:
        return EVEN
    elif a == TOP or b == TOP:
        return TOP
    else:
        return ODD

# Function for parity multiplication operation
def mul_parity(a, b):
    if a == BOTTOM or b == BOTTOM:
        return BOTTOM
    elif a == EVEN or b == EVEN:
        return EVEN
    elif a == TOP or b == TOP:
        return TOP
    else:
        return ODD


# Function to perform parity analysis during multiplication
def mult_parity_analysis(expr, parity_env, var):
    left, right = [x.strip() for x in expr.split("*", 1)]
                 
    # Clean left and right variable names
    #left = clean_variable_name(left)
    

    if left in parity_env:
        left_parity = parity_env[left]
    elif left.isdigit():
        left_parity = parity_of_literal(int(left))
    else:
        left_parity = BOTTOM
    

    #right = clean_variable_name(right)
    if right in parity_env:
        right_parity = parity_env[right]
    elif right.isdigit():
        right_parity = parity_of_literal(int(right))
    else:
        right_parity = BOTTOM
    mult = 1
    if not left.isdigit() and not right.isdigit():
        mult = var_value_env[left] * var_value_env[right]
    elif right.isdigit(): 
        mult = var_value_env[left] * int(right)
    elif left.isdigit():
        mult = int(left) * var_value_env[right]
    elif left.isdigit() and right.isdigit():
        mult = int(left) * int(right)
    var_value_env[var] = mult
    
    parity_env[var] = mul_parity(left_parity, right_parity)

# Function to perform parity analysis during addition
def add_parity_analysis(expr, parity_env, var):
    left, right = [x.strip() for x in expr.split("+", 1)]
    
    #left = clean_variable_name(left)
    #right = clean_variable_name(right)
    sum = 0
    if left in parity_env:
        left_parity = parity_env[left]
    elif left.isdigit():
        left_parity = parity_of_literal(int(left))
    else:
        left_parity = BOTTOM
    

    #right = clean_variable_name(right)
    if right in parity_env:
        right_parity = parity_env[right]
    elif right.isdigit():
        right_parity = parity_of_literal(int(right))
    else:
        right_parity = BOTTOM
    
    if not left.isdigit() and not right.isdigit():
        sum = var_value_env[left] + var_value_env[right]
    elif right.isdigit(): 
        sum = var_value_env[left] + int(right)
    elif left.isdigit():
        sum = int(left) + var_value_env[right]
    elif left.isdigit() and right.isdigit():
        sum = int(left) + int(right)
    var_value_env[var] = sum
    
    parity_env[var] = add_parity(left_parity, right_parity)

# Function to determine the parity of a literal integer
def parity_of_literal(value):
    return EVEN if value % 2 == 0 else ODD

# Function to clean variable names by removing special characters
def clean_variable_name(var_name):
    return re.sub(r'\W+', '', var_name) 

# Function to evaluate and replace innermost expressions 
def evaluate_innermost_expr(expr, parity_env):
    # evaluating innermost expressions until no parentheses remain
    while '(' in expr:
       
        innermost = re.search(r'\(([^()]+)\)', expr)
        if innermost:
            sub_expr = innermost.group(1)  # innermost expression
            temp_var = f"temp_{hash(sub_expr)}"  # unique temporary variable name

            # addition or multiplication
            if '+' in sub_expr:
                add_parity_analysis(sub_expr, parity_env, temp_var)
            elif '*' in sub_expr:
                mult_parity_analysis(sub_expr, parity_env, temp_var)
            else:
                #no recognized operator
                parity_env[temp_var] = BOTTOM

            # replace the evaluated sub-expression with the temporary variable 
            expr = expr[:innermost.start()] + temp_var + expr[innermost.end():]

            parity_env[temp_var] = parity_env[temp_var]
            

    return expr 


#Function for analysis process where needed within cfg analsyis
def process_assignment(node, parity_env):
    # Process assignment statements within if-else branches
    source = node.source()
    if "=" in source: # eg: line: z = a+b
            var, expr = [x.strip() for x in source.split("=", 1)]
            
            if var not in parity_env:
                parity_env[var] = BOTTOM
            # Process the innermost expressions iteratively
            expr = evaluate_innermost_expr(expr, parity_env)
            
            
            if expr.isdigit():  # Check for literal assignment
                parity_env[var] = parity_of_literal(int(expr))
                var_value_env[var] = int(expr)
            elif expr in parity_env:
                parity_env[var] = parity_env[expr]
            elif "+" in expr:  # Handle addition expressions => z = a+b
                add_parity_analysis(expr, parity_env, var)
                
            elif "*" in expr:  # Handle multiplication expressions
                mult_parity_analysis(expr, parity_env, var)
            else:
                parity_env[var] = TOP  # Unknown expression type

            if expr in var_value_env:
                var_value_env[var] = var_value_env[expr]

  
# Function for analyzing parity across CFG nodes
def analyze_parity(cfg):
    
    false_child = 0
    traversed_nodes = []
   
    loopflag = None
  
    for node_id, node in CFGNode.cache.items():
        
        if node_id in traversed_nodes:
            continue


        source = node.source()
        
        if "=" in source: # eg: line: z = a+b
            var, expr = [x.strip() for x in source.split("=", 1)]
            
            if var not in parity_env:
                parity_env[var] = BOTTOM
            # process the innermost expressions iteratively
            expr = evaluate_innermost_expr(expr, parity_env)
            
            if expr in var_value_env:
                var_value_env[var] = var_value_env[expr]

            if expr.isdigit():  # literal assignment
                parity_env[var] = parity_of_literal(int(expr))
                var_value_env[var] = int(expr)

            elif expr in parity_env:
                parity_env[var] = parity_env[expr]
                

            elif "+" in expr:  # Handle addition expressions => z = a+b
                add_parity_analysis(expr, parity_env, var)
                
            elif "*" in expr:  # Handle multiplication expressions
                mult_parity_analysis(expr, parity_env, var)
            else:
                parity_env[var] = TOP  # Unknown expression type
            
            print(f"Node {node_id}: {source}")
            for var, parity in parity_env.items():
                print(f"    {var}: {parity}")
            print("---")

        #if-else handling
        elif source.startswith("_if:"):
            
            
            if_branch_env = parity_env.copy()
            else_branch_env = parity_env.copy()
            
            condition = source[4:].strip()
            false_child = node.children[1].rid
            first_child = node.children[0].rid
            true_nodes = false_child - first_child
           #local environment with parity_env variables directly accessible by their names to help run exec()
            local_env = {var: var_value_env.get(var, BOTTOM) for var in var_value_env}
            
            local_env["condition_result"] = None 

            exec(f"condition_result = bool({condition})", {}, local_env)
            # retrieve the updated condition_result from local_env
            condition_result = local_env["condition_result"]

            if condition_result is True:
                for i in range(first_child,false_child):
                    process_assignment(CFGNode.cache[i], if_branch_env)
                    source = CFGNode.cache[i].source()
                    print(f"loop run for {i}th node")
                    print(f"Node {i}: {source}")
                    for var, parity in if_branch_env.items():
                        print(f"    {var}: {parity}")
                    print("---")
                    
                    traversed_nodes.append(i) 
            elif condition_result is False:
                process_assignment(CFGNode.cache[false_child], else_branch_env)
                source = CFGNode.cache[false_child].source()
                print(f"Else branch - Node {false_child}: {source}")
                for var, parity in else_branch_env.items():
                    print(f"    {var}: {parity}")
                print("---")
                
                traversed_nodes.append(range(first_child,false_child+1))
            
            #meet operation
            for var in if_branch_env.keys() | else_branch_env.keys():  # Union of keys
                parity_env[var] = meet(if_branch_env.get(var, BOTTOM), else_branch_env.get(var, BOTTOM))

            traversed_nodes.append(false_child)
           
            print(f"After if-else merge at Node {node_id}:")
            for var, parity in parity_env.items():
                print(f"    {var}: {parity}")
            print("---")

        elif source.startswith("_while:"): 
            cumulative_env = parity_env.copy()
            while_branch_env = parity_env.copy()
            false_branch_env = parity_env.copy()
            condition = source[7:].strip()
            false_child = node.children[1].rid
            first_child = node.children[0].rid

            #local environment with parity_env variables directly accessible by their names to run exec()
            local_env = {var: var_value_env.get(var, BOTTOM) for var in var_value_env}
                    
            local_env["condition_result"] = None 
            exec(f"condition_result = bool({condition})", {}, local_env)
            condition_result = local_env["condition_result"]

            if condition_result:
                loopflag = True
            count = 1
            total_while_true_childs = false_child - first_child
            while loopflag:
                # print(f"Count: {count}")
                for i in range(first_child,false_child):
                    #updating condition within loop
                    local_env = {var: var_value_env.get(var, BOTTOM) for var in var_value_env}
                    
                    local_env["condition_result"] = None 
                    exec(f"condition_result = bool({condition})", {}, local_env)
                    
                    condition_result = local_env["condition_result"]
                    
                    # if condition_result is True and i == false_child-1:
                    #     loopflag = False
                    if condition_result is True:
                        process_assignment(CFGNode.cache[i], while_branch_env)
                        source = CFGNode.cache[i].source()
                        print(f"loop run for {i}th node")
                        print(f"Node {i}: {source}")
                        for var, parity in while_branch_env.items():
                            print(f"    {var}: {parity}")
                        print("---")
                        traversed_nodes.append(i) 
                        
                    elif condition_result is False:
                        count = -1
                        loopflag = False
                        break

                     #  meet operation after each iteration to capture effects after each iteration
                    for var in while_branch_env.keys():
                        cumulative_env[var] = meet(cumulative_env.get(var, BOTTOM), while_branch_env[var])
                    
                count = count + 1
                
            # Update parity_env with cumulative meet results after loop
            for var in cumulative_env.keys():
                if cumulative_env[var]== TOP:
                    parity_env[var] = cumulative_env[var]

            # variables with a clear final state we can assign its final state here
            for var in while_branch_env.keys():
                if cumulative_env[var] != TOP:
                    parity_env[var] = while_branch_env[var]

            # the merged environment after the if-else
            print(f"After while loop at Node {node_id}:")
            for var, parity in parity_env.items():
                print(f"    {var}: {parity}")
            print("---")
            continue   

        elif source.startswith("_for:"):

            for_branch_env = parity_env.copy()
            condition_fail_branch_env = parity_env.copy()
            cumulative_env = parity_env.copy()
            

            #content of for loop
            source = CFGNode.cache[node_id+1].source()
            
        
            loop_var, range_expr = [part.strip() for part in source.split("=", 1)]
            # remove any ".shift()" part from the range expression
            range_expr = range_expr.split(".shift()")[0]

            loop_var = loop_var.strip()  
            range_expr = range_expr.strip() 

            loop_range = eval(range_expr)
            
            
            loopflag = True
            count = 1  
           
            false_child = node.children[1].rid
            first_child = node.children[0].rid
            
            traversed_nodes = []  # keep track of nodes that are visited
          
            traversed_nodes.append(node_id+1)
            for val in loop_range:
               
                var_value_env[loop_var] = val
              
                # each node in the loop body 
                for i in range(first_child+1, false_child):
                                       
                    # whether to proceed with processing the current loop body node
                    
                    if val<=loop_range[-1]:
                        condition_result= True  
                    else:
                        condition_result = False
                    # if still in the loop range
                    if condition_result is True:
                        process_assignment(CFGNode.cache[i], for_branch_env)
                        
                        source = CFGNode.cache[i].source()
                        
                        print(f"loop run for {i-1}th node in {loop_var} = {val}")
                        print(f"Node {i-1}: {source}")
                        for var, parity in for_branch_env.items():
                            print(f"    {var}: {parity}")  #  variable parities
                        print("---")
                        
                        traversed_nodes.append(i)
                    else:
                        loopflag = False
                        break  
                # meet operation after each iteration to capture cumulative effects in `cumulative_env`
                for var in for_branch_env.keys():
                    cumulative_env[var] = meet(cumulative_env.get(var, BOTTOM), for_branch_env[var])
        
                count += 1
             
            # update parity_env with cumulative meet results after loop
            for var in cumulative_env.keys():
                parity_env[var] = cumulative_env[var]

            traversed_nodes.append(false_child)
            # Print the merged environment after the if-else
            print(f"After for loop merge at Node {node_id}:")
            for var, parity in parity_env.items():
                print(f"    {var}: {parity}")
            print("---")

            
        #print the parities even if its not a node of above categories
        else:
            print(f"Node {node_id}: {source}")
            for var, parity in parity_env.items():
                print(f"    {var}: {parity}")
            print("---") 

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('pythonfile')
    args = parser.parse_args()
    arcs = []

    pythonfile = args.pythonfile
    cfg = PyCFG()
    
    cfg.gen_cfg(slurp(pythonfile).strip())
    g = CFGNode.to_graph(arcs)
    g.draw(args.pythonfile + '.png', prog ='dot') 

    analyze_parity(cfg)

