import textwrap
from Bio.Seq import Seq
from Bio.SeqFeature import SeqFeature, FeatureLocation
from Bio.PDB.Polypeptide import aa1, aa3
from Bio import SeqIO

try:
    from BCBio import GFF
except ImportError:

    class GFF:
        def parse(*a):
            """Not available. Please install bcbio-gff."""
            raise ImportError("Please install the bcbio-gff library to parse GFF data")


def _load_gff_with_all_features(path):
    """Custom function to load a GFF file and gather all features."""
    
    records = list(GFF.parse(path))
    print(f"DEBUG: GFF parse returned {len(records)} records")
    
    combined_record = records[0]  # start with the first record
    print(f"DEBUG: First record has {len(combined_record.features)} features")
    
    all_features = []
    for i, feature in enumerate(combined_record.features):
        print(f"DEBUG: Feature {i}: {feature.type} at {feature.location.start}-{feature.location.end}")
        print(f"DEBUG: Feature {i} qualifiers: {feature.qualifiers}")

        # Add main feature
        all_features.append(feature)
        
        # Check for sub-features
        if hasattr(feature, 'sub_features'):
            print(f"DEBUG: Feature {i} has {len(feature.sub_features)} sub-features")
            all_features.extend(feature.sub_features)
            for j, sub_feature in enumerate(feature.sub_features):
                print(f"DEBUG: Sub-feature {j}: {sub_feature.type} at {sub_feature.location.start}-{sub_feature.location.end}")
    
    # Assign all features to the combined record
    combined_record.features = all_features

    # Check if there are more records
    for i, additional_record in enumerate(records[1:]):
        print(f"DEBUG: Additional record {i+1} has {len(additional_record.features)} features")
        combined_record.features.extend(additional_record.features)
    
    return combined_record


def complement(dna_sequence):
    """Return the complement of the DNA sequence.

    For instance ``complement("ATGCCG")`` returns ``"TACGGC"``.

    Uses BioPython for speed.
    """
    return str(Seq(dna_sequence).complement())


def reverse_complement(sequence):
    """Return the reverse-complement of the DNA sequence.

    For instance ``complement("ATGCCG")`` returns ``"GCCGTA"``.

    Uses BioPython for speed.
    """
    return complement(sequence)[::-1]


if type(aa1) is str and type(aa3) is list:
    # biopython before 1.80
    aa_short_to_long_form_dict = {
        _aa1: _aa3[0] + _aa3[1:].lower() for (_aa1, _aa3) in zip(aa1 + "*", aa3 + ["*"])
    }
else:
    # type is tuple
    # biopython 1.80 and later
    # See issue #73
    # relevant biopython commit: https://github.com/biopython/biopython/commit/257143be9196b77619d3d8cadc22039212681e08
    aa_short_to_long_form_dict = {
        _aa1: _aa3[0] + _aa3[1:].lower()
        for (_aa1, _aa3) in zip(aa1 + ("*",), aa3 + ("*",))
    }


def translate(dna_sequence, long_form=False):
    """Translate the DNA sequence into an amino-acids sequence MLKYQT...

    If long_form is true, a list of 3-letter amino acid representations
    is returned instead (['Ala', 'Ser', ...]).
    """
    result = str(Seq(dna_sequence).translate())
    if long_form:
        result = [aa_short_to_long_form_dict[aa] for aa in result]
    return result


def extract_graphical_translation(sequence, location, long_form=False):
    """Return a string of the "graphical" translation of a sequence's subsegment.

    Here "graphical" means that the amino acid sequence is always given
    left-to-right, as it will appear under the sequence in the plot. This matters
    when the location is on the -1 strand. In this case, the amino-acids are
    determined by (part of) the reverse-complement of the sequence, however
    the sequence returned will be the mirror of the translated sequence, as
    this is the left-to-right order in which the codons corresponding to the
    amino-acids appear in the sequence.

    Parameters
    ----------
    sequence
      An "ATGC" string.

    location
      Either (start, end) or (start, end, strand), with strand in (0, 1, -1).

    long_form
      if True, a list of 3-letter amino acid representations is returned instead
      (['Ala', 'Ser', ...]).

    """
    if len(location) == 3:
        start, end, strand = location
    else:
        start, end = location
        strand = 1
    subsequence = sequence[start:end]
    if strand == -1:
        subsequence = reverse_complement(subsequence)
    translation = translate(subsequence, long_form=long_form)
    if strand == -1:
        translation = translation[::-1]
    return translation


def load_record(path, filetype=None):
    """Load a Genbank file.

    Parameters
    ----------
    path
      Path to record.

    filetype
      Filetype; one of "genbank" or "gff". Default None infers from extension.
    """
    if filetype is None:
        if isinstance(path, str):
            # Input is a file path
            if path.lower().endswith(".gff"):
                return _load_gff_with_all_features(path)
            else:
                return SeqIO.read(path, "genbank")
        else:
            # Input is a file-like object
            try:
                return SeqIO.read(path, "genbank")
            except:
                path.seek(0)
                return _load_gff_with_all_features(path)
    elif filetype == "genbank":
        return SeqIO.read(path, "genbank")
    elif filetype == "gff":
        return _load_gff_with_all_features(path)
    else:
        raise ValueError("'Filetype' must be one of 'genbank' or 'gff'.")


def annotate_biopython_record(
    seqrecord, location="full", feature_type="misc_feature", margin=0, **qualifiers
):
    """Add a feature to a Biopython SeqRecord.

    Parameters
    ----------

    seqrecord
      The biopython seqrecord to be annotated.

    location
      Either (start, end) or (start, end, strand). (strand defaults to +1)

    feature_type
      The type associated with the feature.

    margin
      Number of extra bases added on each side of the given location.

    qualifiers
      Dictionary that will be the Biopython feature's `qualifiers` attribute.
    """
    if location == "full":
        location = (margin, len(seqrecord) - margin)

    strand = location[2] if len(location) == 3 else 1
    seqrecord.features.append(
        SeqFeature(
            FeatureLocation(location[0], location[1], strand),
            qualifiers=qualifiers,
            type=feature_type,
        )
    )


def find_narrowest_text_wrap(text, max_line_length):
    """Wrap the text into a multi-line text minimizing the longest line length.

    This is done by first wrapping the text using max_line_length, then
    attempt new wraps by iteratively decreasing the line_length, as long as the
    number of lines stays the same as with max_line_length.
    """
    narrowest_wrap = textwrap.wrap(text, max_line_length)
    narrowest_width = max([len(l) for l in narrowest_wrap])
    for line_length in range(max_line_length - 1, 0, -1):
        wrap = textwrap.wrap(text, line_length)
        if len(wrap) <= len(narrowest_wrap):
            width = max([len(l) for l in wrap])
            if width < narrowest_width:
                narrowest_wrap = wrap
                narrowest_width = width
        else:
            break
    return "\n".join(narrowest_wrap)