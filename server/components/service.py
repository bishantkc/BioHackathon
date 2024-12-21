# def predict_trait(parent1, parent2):
#     """
#     Predict trait based on alleles of two parents.
#     """
#     combinations = [a1 + a2 for a1 in parent1 for a2 in parent2]
#     probabilities = {}
    
#     for combo in combinations:
#         sorted_combo = "".join(sorted(combo))  # BB is the same as Bb
#         probabilities[sorted_combo] = probabilities.get(sorted_combo, 0) + 1
    
#     total = sum(probabilities.values())
#     for genotype in probabilities:
#         probabilities[genotype] = (probabilities[genotype] / total) * 100

#     return probabilities

def cross_alleles(parent1_alleles, parent2_alleles):
    """
    Perform criss-cross inheritance (Punnett square) and return possible combinations.
    """
    combinations = []
    
    for allele1 in parent1_alleles:
        for allele2 in parent2_alleles:
            combinations.append(allele1 + allele2)
    
    return combinations

def predict_trait(parent1: str, parent2: str, trait_name: str) -> dict:
    """
    Predict genetic traits based on the alleles of two parents for the specified trait.
    Assumes the input is in the form of 'BB', 'Bb', 'Tt', etc., where 'B' is dominant and 'b' is recessive.
    """
    # Define basic trait mappings (just for example)
    trait_mapping = {
        "Eye Color": {"dominant_trait": "Brown eyes", "recessive_trait": "Blue eyes"},
        "Hair Type": {"dominant_trait": "Curly hair", "recessive_trait": "Straight hair"}
    }

    if trait_name not in trait_mapping:
        return {"error": "Unknown trait"}

    # Split parents' genotypes into individual alleles
    parent1_alleles = [parent1[i:i+2] for i in range(0, len(parent1), 2)]
    parent2_alleles = [parent2[i:i+2] for i in range(0, len(parent2), 2)]
    
    # Perform criss-cross inheritance (Punnett square)
    possible_combinations = cross_alleles(parent1_alleles, parent2_alleles)
    
    # Calculate the number of dominant and recessive traits in the combinations
    dominant_count = sum(1 for combo in possible_combinations if 'B' in combo)  # Dominant trait (e.g., 'B')
    recessive_count = len(possible_combinations) - dominant_count  # Recessive trait (e.g., 'b')

    # Prepare the result with predictions
    result = {
        "trait_name": trait_name,
        "predictions": [
            {"trait": trait_mapping[trait_name]["dominant_trait"], "probability": (dominant_count / len(possible_combinations)) * 100},
            {"trait": trait_mapping[trait_name]["recessive_trait"], "probability": (recessive_count / len(possible_combinations)) * 100}
        ]
    }
    
    return result




