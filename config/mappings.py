# the household table first: it is the grid for the others
from config.variables import *


class Mappings(Namespace):
    """Every mapping, in the order they must be written; Mappings.all() keeps that order."""
    kind = Mapping

    HOUSEHOLD_PERSON = make_spell_mapping(
        links = HH_SPELL, dataset = Datasets.gbahuishoudenbus, grid = compute_calendar)
    
    ADDRESS_PERSON = make_spell_mapping(
        links = ADDRESS_SPELL, dataset = Datasets.gbaadresobjectbus)
    
    SECM_PERSON = make_spell_mapping(
        links = SECM_SPELL, dataset = Datasets.secmbus)
    
    JOB_PERSON = make_spell_mapping(
        links = JOB_SPELL, dataset = Datasets.spolisbus)
    
    BREADWINNER_PERSON = Mapping(
        unit = BREADWINNER | PERSON | YEAR,
        recipe = lambda y: Datasets.koppelpersoonhuishouden.read(columns = [], year = y),
        dataset = Datasets.koppelpersoonhuishouden)
    
    MONTHS = Mapping(
        unit = MONTH, 
        recipe = compute_calendar,
        dataset = Datasets.gas_profile
    )