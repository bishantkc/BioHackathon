from fastapi import APIRouter, HTTPException
from Bio import Entrez

router = APIRouter()



Entrez.email = "bishantkc888@gmail.com"


# @router.get("/get_gene_info")
# async def get_gene_info(gene_name: str):
#     # Search for the gene in the Gene database
#     handle = Entrez.esearch(db="gene", term=gene_name)
#     record = Entrez.read(handle)
#     handle.close()

#     # Get the Gene ID (GI)
#     gene_ids = record["IdList"]
#     if not gene_ids:
#         return {"error": "Gene not found"}

#     # Fetch detailed information for the gene
#     handle = Entrez.efetch(db="gene", id=gene_ids[0], retmode="xml")
#     gene_info = Entrez.read(handle)
#     handle.close()

#     # Fetch the sequence of the gene from the Nucleotide database
#     handle = Entrez.esearch(db="nucleotide", term=gene_name, retmax=1)
#     record = Entrez.read(handle)
#     handle.close()

#     sequence_id = record["IdList"][0]

#     # Fetch the sequence in FASTA format
#     handle = Entrez.efetch(
#         db="nucleotide", id=sequence_id, rettype="fasta", retmode="text"
#     )
#     sequence_data = handle.read()
#     handle.close()

#     return {"gene_info": gene_info, "sequence": sequence_data}


@router.get("/get_genes_info")
async def get_genes_info(gene_name: str):
    try:
        # Search for the gene in the Gene database
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

            # Safely handle location and aliases
            location = (
                gene_gene.get("Gene-ref_maploc", "No location available")
                if isinstance(gene_gene.get("Gene-ref_maploc", None), str)
                else "No location available"
            )
            aliases = (
                gene_gene.get("Gene-ref_syn", ["No aliases available"])
                if isinstance(gene_gene.get("Gene-ref_syn", None), list)
                else ["No aliases available"]
            )

            # Safely handle lineage
            lineage_data = (
                gene_data.get("Entrezgene_source", {})
                .get("BioSource", {})
                .get("BioSource_org", {})
                .get("Org-ref", {})
                .get("Org-ref_orgname", {})
                .get("OrgName", {})
            )
            lineage = lineage_data.get("OrgName_lineage", "Unknown lineage")
            # Fetch the genomic sequence from the Nucleotide database
            handle = Entrez.esearch(
                db="nucleotide", term=f'"{gene_name}"[Gene Name]', retmax=1
            )
            nucleotide_record = Entrez.read(handle)
            handle.close()

            # Get the sequence ID (this is usually related to the gene)
            sequence_id = (
                nucleotide_record["IdList"][0]
                if nucleotide_record["IdList"]
                else None
            )
            if not sequence_id:
                sequence_data = "Sequence not found"
            else:
                handle = Entrez.efetch(
                    db="nucleotide",
                    id=sequence_id,
                    rettype="fasta",
                    retmode="text",
                )
                sequence_data = handle.read()
                handle.close()

            # Return all the information
            return {
                "gene_id": gene_id,
                "gene_name": gene_name,
                "official_full_name": description,
                "summary": summary,
                "location": location,
                "aliases": aliases,
                "lineage": lineage,
                "sequence": sequence_data,
            }

        # If no genes match, return a suitable message
        return {"error": f"No exact match found for gene name: {gene_name}"}

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error processing gene info: {e}"
        )


@router.get("/get_protein_info")
async def get_protein_info(protein_name: str):
    try:
        # Search for the protein in the Protein database
        handle = Entrez.esearch(
            db="protein", term=f'"{protein_name}"[All Fields]', retmax=1
        )
        record = Entrez.read(handle)
        handle.close()

        # Get the Protein ID(s) from the search result
        protein_ids = record["IdList"]
        if not protein_ids:
            raise HTTPException(status_code=404, detail="Protein not found")

        # Fetch detailed information for the Protein
        protein_id = protein_ids[0]
        handle = Entrez.efetch(
            db="protein", id=protein_id, rettype="gb", retmode="xml"
        )
        protein_info = Entrez.read(handle)
        handle.close()

        # Extract relevant protein information
        protein_data = protein_info[
            0
        ]  # Assuming the first entry contains the data
        protein_description = protein_data.get(
            "GBSeq_definition", "No description available"
        )
        protein_length = protein_data.get("GBSeq_length", "Unknown length")
        protein_accession = protein_data.get(
            "GBSeq_primary-accession", "Unknown accession"
        )
        protein_source = protein_data.get("GBSeq_source", "Unknown source")

        # Protein Function
        protein_function = protein_data.get(
            "GBSeq_comment", "No function information available"
        )

        # Taxonomy (Organism Information)
        taxonomy_info = protein_data.get(
            "GBSeq_taxonomy", "No taxonomy information available"
        )

        # Fetch the protein sequence in FASTA format
        handle = Entrez.efetch(
            db="protein", id=protein_id, rettype="fasta", retmode="text"
        )
        protein_sequence = handle.read()
        handle.close()

        # Return the protein information
        return {
            "protein_id": protein_id,
            "definition": protein_description,
            "length": protein_length,
            "accession": protein_accession,
            "source": protein_source,
            "organism": taxonomy_info,
            "comment": protein_function,
            "sequence": protein_sequence,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error processing protein info: {e}"
        )
