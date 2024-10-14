'''
Flexible classes to represent tables, records & links in the data request,
as obtained from the Airtable json "raw export" of data request content.

The purpose is to create generic objects allowing intuitive navigation/coding
of the data request "network" (i.e., linked records). While the dict variables from
the export can be used directly for this, manipulating them is more complex and
error-prone.

Each record from a table is represented as a dreq_record object.
The object's attribute names are determined automatically from the Airtable field
names, which are the names of table columns in Airtable, following simple formatting
rules (e.g. change space to underscore). Original names of Airtable fields
are stored as well, allowing unambiguous comparison with Airtable content.
'''

from dataclasses import dataclass
from dataclasses import field as dataclass_field  # "field" is used often for Airtable column names

UNIQUE_VAR_NAME = 'compound name'  # method used to uniquely name variables

def format_attribute_name(k):
    '''
    Adjust input string so that it's suitable for use as an object attribute name using the dot syntax (object.attribute).
    '''
    k = k.strip()
    k = k.lower()
    substitute = {
        # replacement character : [characters to replace with the replacement character]
        '_' : [' ', '.', '#'],
        '' : ['(', ')', ',']
    }
    for replacement in substitute:
        for s in substitute[replacement]:
            k = k.replace(s, replacement)
    return k

###############################################################################
# Generic classes
# (not specific to different data request tables)

@dataclass
class dreq_link:
    '''
    Generic class to represent a link to a record in a table.

    The table_id, record_id reference the record. They are used to locate a record.
    '''
    table_id : str
    record_id : str
    table_name : str  # useful as a human-readable lable
    # record_name : str  # not all tables have a "name" attribute, so would need to choose this based on table

    def __repr__(self):
        # return self.record_id
        return f'link: table={self.table_name}, record={self.record_id}'

class dreq_record:
    '''
    Generic class to represent a single record from a table.
    '''
    def __init__(self, record, field_info):
        # Loop over fields in the record
        for field_name, value in record.items():

            # Check if the field contains links to records in other tables
            if 'linked_table_id' in field_info[field_name]:
                assert isinstance(value, list), 'links should be a list of record identifiers'
                for m, record_id in enumerate(value):
                    # Change the record_id str into a more informative object representing the link
                    d = {
                        'table_id' : field_info[field_name]['linked_table_id'],
                        'table_name' : field_info[field_name]['linked_table_name'],
                        'record_id' : record_id,
                        # 'record_name' : '', # fill this in later if desired (finding it here would require access to whole base)
                    }
                    value[m] = dreq_link(**d)

            # Adjust the field name so that it's accessible as an object attribute using the dot syntax (object.attribute)
            key = field_info[field_name]['attribute_name']
            assert not hasattr(self, key), f'for field {field_name}, key already exists: {key}'
            setattr(self, key, value)

    def __repr__(self):
        # return pprint.pformat(vars(self))
        l = []
        show_list_entries = 2
        for k,v in self.__dict__.items():
            s = f'  {k}: ' 
            if isinstance(v, list):
                # If attribute is a list of links, show only show_list_entries of them.
                # This makes it easier to view records that contain very long lists of links.
                indent = ' '*len(s)
                n = len(v)
                s += f'{v[0]}'
                for m in range(1, min(show_list_entries,n)):
                    s += '\n' + indent + f'{v[m]}'
                if n > show_list_entries:
                    # s += '\n' + indent + f'... ({n} entries)'
                    s += '\n' + indent + f'... ({n} in list, first {show_list_entries} shown)'
            else:
                # Attribute is just a regular string or number.
                s = f'{s}{v}'
            l.append(s)
        return '\n' + '\n'.join(l)

class dreq_table:
    '''
    Generic class to represent an table from the data request Airtable raw export json file (dict).

    Here both "field" and "attribute" are used to refer to the columns in the table.
    "field"  refers to the name of a column as it appears in Airtable.
    "attribute" refers to the name of the column converted to the name of a record object attribute.
    '''
    def __init__(self, table, table_id2name):

        # Set attributes that describe the table
        self.table_id = table['id']
        self.table_name = table['name']
        self.base_id = table['base_id']
        self.base_name = table['base_name']
        self.description = table['description']

        # Get info about fields (columns) in the table records, which are used below when creating record objects
        fields = table['fields'] # dict giving info on each field, keyed by field_id (example: 'fld61d8b5mzI45H8F')
        field_info = {field['name'] : field for field in fields.values()} # as fields dict, but use field name as the key
        assert len(fields) == len(field_info), 'field names are not unique!' 
        # (since field names are keys in record dicts, their names should be unique)
        attr2field = {}
        links = {}
        for field_name, field in field_info.items():
            # Determine an attribute name for the field.
            # The field name is the name from Airtable, but it may include spaces or other forbidden characters.
            attr = format_attribute_name(field_name)
            field['attribute_name'] = attr
            attr2field[attr] = field_name  # remember the Airtable name, in case useful later
            # If field is a link, add the name of the linked table to field_info.
            if 'linked_table_id' in field:
                field['linked_table_name'] = table_id2name[field['linked_table_id']]
                links[attr] = field['linked_table_name']

        # Loop over records to create a record object representing each one
        records = table['records'] # dict giving info on each record, keyed by record_id (example: 'reczyxsKbAseqCisA')
        for record_id, record in records.items():
            if len(record) == 0:
                # don't allow empty records!
                # print(f'skipping empty record {record_id} in table {self.table_name}')
                continue
            # Replace record dict with a record object
            records[record_id] = dreq_record(record, field_info)

        # attributes for the collection of records (table rows)
        self.records = records
        self.record_ids = list(self.records.keys())
        self.nrec = len(self.record_ids)

        # attributes describing the attributes (columns) in each individual record
        self.field_info = field_info
        self.attr2field = attr2field
        self.links = links

    def rename_attr(self, old, new):
        if old in self.attr2field:
            assert new not in self.attr2field

            field_name = self.attr2field[old]
            self.field_info[field_name]['attribute_name'] = new

            self.attr2field[new] = self.attr2field[old]
            self.attr2field.pop(old)

            if old in self.links:
                self.links[new] = self.links[old]
                self.links.pop(old)

            for record in self.records.values():
                if not hasattr(record, old):
                    continue
                setattr(record, new, getattr(record, old))
                delattr(record, old)

    def __repr__(self):
        #return f'Table: {self.table_name}, records: {self.nrec}'
        s = f'table: {self.table_name}'
        s += f'\ndescription: {self.description}'
        s += f'\nrecords (rows): {self.nrec}'
        s += '\nattributes (columns): ' + ', '.join(sorted(self.attr2field))
        if len(self.links) > 0:
            s += '\nlinks to other tables:' # ({}):'.format(len(self.links))
            for attr, target in sorted(self.links.items()):
                s += f'\n  {attr} -> {target}'
        return s

    def get_record(self, m):
        return self.records[self.record_ids[m]]
    
    def delete_record(self, record_id):
        self.records.pop(record_id)
        self.record_ids.remove(record_id)
        self.nrec -= 1

###############################################################################
# Non-generic classes, i.e. they have a specific function in the data request

@dataclass
class expt_request:
    '''
    Object to store variables requested for an experiment.
    Variable names are stored in seperate sets for different priority levels.
    '''
    experiment : str
    high : set[str] = dataclass_field(default_factory=set)
    medium : set[str] = dataclass_field(default_factory=set)
    low : set[str] = dataclass_field(default_factory=set)

    def __post_init__(self):
        self.consistency_check()

    def add_vars(self, var_names, priority_level):
        '''
        Add variables to output from the experiment, at the specified priority level.
        Removes overlaps between priority levels (e.g., if adding a variable at high
        priority that is already requested at medium priority, it is removed from the
        medium priority list).
        
        Parameters
        ----------
        var_names : set
            Set of unique variable names to be added.
        priority_level : str
            Priority level at which to add them.
            Not case sensitive (will be rendered as lower case).

        Returns
        -------
        expt_request object is updated with the new variables, and any overlaps removed.
        '''
        priority_level = priority_level.lower()
        current_vars = getattr(self, priority_level)
        current_vars.update(var_names)
        # Remove any overlaps by ensuring a variable only appears at its highest
        # requested priority level.
        self.medium = self.medium.difference(self.high) # remove any high priority vars from medium priority group
        self.low = self.low.difference(self.high) # remove any high priority vars from low priority group
        self.low = self.low.difference(self.medium) # remove any medium priority vars from low priority group
        self.consistency_check()

    def consistency_check(self):
        # Confirm that priority sets don't overlap
        assert self.high.intersection(self.medium.union(self.low)) == set()
        assert self.medium.intersection(self.high.union(self.low)) == set()
        assert self.low.intersection(self.high.union(self.medium)) == set()
        # Also confirm object contains the expected priority levels
        pl = list(vars(self))
        pl.remove('experiment')
        assert set(pl) == {'high', 'medium', 'low'}

    def __repr__(self):
        self.consistency_check()
        break_up_compound_name = not True
        l = [f'Variables (by priority) for experiment: {self.experiment}']
        for p in ['high', 'medium', 'low']:
            req = getattr(self, p)
            if len(req) == 0:
                continue
            n = len(req)
            s = f'  {p} ({n}): '
            indent = ' '*len(s)
            sortby = str.lower
            req = sorted(req, key=sortby)
            if break_up_compound_name and UNIQUE_VAR_NAME == 'compound name':
                # for better readability, show all vars in each cmor table on one line
                separator = '.'
                lt = [tuple(varname.split(separator)) for varname in req]
                tables = sorted(set([t[0] for t in lt]), key=sortby)
                req = []
                for table in tables:
                    varnames = sorted(set([t[1] for t in lt if t[0] == table]), key=sortby)
                    n = len(varnames)
                    req.append(f'{table} ({n}): ' + ', '.join(varnames))
            s += req[0]
            for varname in req[1:]:
                s += '\n' + indent + varname
            l.append(s)
        return '\n'.join(l)

    def to_dict(self):
        '''
        Return dict equivalent of the object, suitable to write to json.
        '''
        sortby = str.lower
        return {
            self.experiment : {
                'High' : sorted(self.high, key=sortby),
                'Medium' : sorted(self.medium, key=sortby),
                'Low' : sorted(self.low, key=sortby),
            }
        }
