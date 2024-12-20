from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from components.traits.service import predict_trait

router = APIRouter()


# Define request and response models
class GeneticTraitsRequest(BaseModel):
    parent1: str
    parent2: str
    trait_name: str
    dominant_trait: str
    recessive_trait: str


class GeneticTraitsResponse(BaseModel):
    trait_name: str
    predictions: list[dict]


@router.post("/genetic-traits")
async def predict_genetic_traits(parent1: str, parent2: str, trait_name: str):
    """
    Predict genetic traits based on the alleles of two parents for the specified trait.
    """
    result = predict_trait(parent1, parent2, trait_name)
    return result


import requests


def get_gene_info(gene_name):
    url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=gene&term={gene_name}[Gene]+AND+human[organism]&retmode=xml"
    response = requests.get(url)

    if response.status_code == 200:
        # Parse XML response and extract relevant data
        return response.text  # You can parse and extract specific data here
    else:
        return None


def get_protein_info(protein_id):
    url = f"https://www.uniprot.org/uniprot/{protein_id}.xml"
    response = requests.get(url)

    if response.status_code == 200:
        return response.text  # XML response containing protein information
    else:
        return None


class GeneProteinInfo(BaseModel):
    gene_name: str
    gene_info: str
    protein_id: str
    protein_info: str


@router.get("/gene_protein_info", response_model=GeneProteinInfo)
async def get_gene_protein_info(gene_name: str, protein_id: str):
    # Fetch gene info from NCBI
    gene_info = get_gene_info(gene_name)

    # Fetch protein info from UniProt
    protein_info = get_protein_info(protein_id)

    # Return the combined data
    return GeneProteinInfo(
        gene_name=gene_name,
        gene_info=gene_info,
        protein_id=protein_id,
        protein_info=protein_info,
    )


from Bio import Entrez


Entrez.email = "bishantkc888@gmail.com"


@router.get("/get_gene_info")
async def get_gene_info(gene_name: str):
    # Search for the gene in the Gene database
    handle = Entrez.esearch(db="gene", term=gene_name)
    record = Entrez.read(handle)
    handle.close()

    # Get the Gene ID (GI)
    gene_ids = record["IdList"]
    if not gene_ids:
        return {"error": "Gene not found"}

    # Fetch detailed information for the gene
    handle = Entrez.efetch(db="gene", id=gene_ids[0], retmode="xml")
    gene_info = Entrez.read(handle)
    handle.close()

    # Fetch the sequence of the gene from the Nucleotide database
    handle = Entrez.esearch(db="nucleotide", term=gene_name, retmax=1)
    record = Entrez.read(handle)
    handle.close()

    sequence_id = record["IdList"][0]

    # Fetch the sequence in FASTA format
    handle = Entrez.efetch(
        db="nucleotide", id=sequence_id, rettype="fasta", retmode="text"
    )
    sequence_data = handle.read()
    handle.close()

    return {"gene_info": gene_info, "sequence": sequence_data}


@router.get("/get_genes_info")
async def get_genes_info(gene_name: str):
    try:
        # Search for the gene in the Gene database, focusing on the official symbol
        handle = Entrez.esearch(
            db="gene", term=f'"{gene_name}"[Gene Name]'
        )  # Exact match to the Gene Name
        record = Entrez.read(handle)
        handle.close()

        # Get the Gene ID(s) from the search result
        gene_ids = record["IdList"]
        if not gene_ids:
            raise HTTPException(status_code=404, detail="Gene not found")

        # Loop through gene IDs to fetch detailed information for each gene
        for gene_id in gene_ids:
            handle = Entrez.efetch(db="gene", id=gene_id, retmode="xml")
            gene_info = Entrez.read(handle)
            handle.close()

            # Extract basic gene information
            gene_data = gene_info[
                0
            ]  # Assuming the first entry contains the data
            gene_track = gene_data.get("Entrezgene_track-info", {}).get(
                "Gene-track", {}
            )
            gene_id = gene_track.get("Gene-track_geneid", "Unknown")

            # Additional parsing for specific fields
            gene_gene = gene_data.get("Entrezgene_gene", {}).get(
                "Gene-ref", {}
            )
            gene_name = gene_gene.get(
                "Gene-ref_locus", "No gene name available"
            )
            description = gene_gene.get(
                "Gene-ref_desc", "No description available"
            )

            summary = gene_data.get(
                "Entrezgene_summary", "No summary available"
            )

            # Return the first valid result with the summary
            location = gene_gene.get(
                "Gene-ref_maploc", "No location available"
            )

            # Return the first valid result with all the information
            return {
                "gene_id": gene_id,
                "gene_name": gene_name,
                "description": description,
                "summary": summary,
                "location": location,
            }

        # If no genes match, return a suitable message
        return {"error": f"No exact match found for gene name: {gene_name}"}

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error processing gene info: {e}"
        )


# @router.get("/get_gene_info")
# async def get_gene_info(gene_name: str):
#     # Search for the gene in the Gene database
#     handle = Entrez.esearch(db="gene", term=gene_name)
#     record = Entrez.read(handle)
#     handle.close()

#     # Get the Gene ID (GI) from search result
#     gene_ids = record["IdList"]
#     if not gene_ids:
#         return {"error": "Gene not found"}

#     # Fetch detailed gene information (focus on essential data)
#     handle = Entrez.efetch(db="gene", id=gene_ids[0], retmode="xml")
#     gene_info = Entrez.read(handle)
#     handle.close()

#     # Print raw data (optional for debugging)
#     # print(gene_info)

#     # Extract useful information (handle missing keys)
#     useful_gene_info = {
#         "gene_name": gene_info[0].get("Entrezgene_gene", {}).get("Gene-ref_locus", "Gene Name Not Available"),
#         "chromosome_location": gene_info[0].get("Entrezgene_maploc", "Location Not Available"),
#         "description": gene_info[0].get("Entrezgene_summary", "Description Not Available"),
#     }

#     # Fetch the gene sequence (FASTA format)
#     handle = Entrez.esearch(db="nucleotide", term=gene_name, retmax=1)
#     record = Entrez.read(handle)
#     handle.close()

#     sequence_id = record["IdList"][0]

#     # Fetch the sequence in FASTA format
#     handle = Entrez.efetch(db="nucleotide", id=sequence_id, rettype="fasta", retmode="text")
#     sequence_data = handle.read()
#     handle.close()

#     gene_dinfo = await get_genes_info("BRCA1")
#     print("Gene Information:", gene_dinfo)

#     return {
#         "gene_info": useful_gene_info,
#         "sequence": sequence_data
#     }


@router.get("/get_genee_info")
async def get_genee_info(gene_name: str):
    try:
        # Search for the gene in the Gene database
        handle = Entrez.esearch(db="gene", term=gene_name)
        record = Entrez.read(handle)
        handle.close()

        # Get Gene IDs from the search result
        gene_ids = record["IdList"]
        if not gene_ids:
            raise HTTPException(status_code=404, detail="Gene not found")

        # Iterate through gene IDs to fetch detailed gene info
        for gene_id in gene_ids:
            handle = Entrez.efetch(db="gene", id=gene_id, retmode="xml")
            gene_info = Entrez.read(handle)
            handle.close()

            # Extract the required gene details from the fetched data
            gene_data = gene_info[0]
            gene_details = gene_data.get("Entrezgene_gene", {})

            # Extract relevant fields
            gene_name = gene_details.get("Gene-ref", {}).get(
                "Gene-ref_locus", "No gene name available"
            )
            description = gene_details.get("Gene-ref", {}).get(
                "Gene-ref_desc", "No description available"
            )

            # Get the aliases of the gene
            aliases = gene_details.get("Gene-ref", {}).get("Gene-ref_syn", [])

            # Get gene type (e.g., protein coding)
            gene_type = gene_details.get("Gene-ref", {}).get(
                "Gene-ref_type", "No gene type available"
            )

            # Return the extracted information
            return {
                "gene_id": gene_id,
                "gene_name": gene_name,
                "description": description,
                "aliases": aliases,
                "gene_type": gene_type,
            }

        # If no genes match
        return {"error": f"No exact match found for gene name: {gene_name}"}

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error processing gene info: {e}"
        )
