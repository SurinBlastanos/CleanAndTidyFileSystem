#test regipy

import json
import os
from tempfile import mkdtemp

#import pytest
from regipy import RegistryParsingException, attr
from regipy.hive_types import NTUSER_HIVE_TYPE
from regipy.plugins.utils import dump_hive_to_json

from regipy.recovery import apply_transaction_logs
from regipy.regdiff import compare_hives
from regipy.registry import RegistryHive, NKRecord, LIRecord, Subkey, logger
from regipy.utils import convert_wintime

def recurse_subkeys(self,numSiblings=0, depth = 0, nk_record=None, path=None, as_json=False, is_init=True):
    """
    Recurse over a subkey, and yield all of its subkeys and values
    :param nk_record: an instance of NKRecord from which to start iterating, if None, will start from Root
    :param path: The current registry path
    :param as_json: Whether to normalize the data as JSON or not
    """
    # If None, will start iterating from Root NK entry
    if not nk_record:
        nk_record = self.root

    # Iterate over subkeys
    if nk_record.header.subkey_count:
        #itr = 0
        for subkey in nk_record.iter_subkeys():
            #if(depth==1):
                #print("itr:"+str(itr)+"/"+str(numSiblings))
            #itr = itr+1
            if path:
                subkey_path = r'{}\{}'.format(path, subkey.name) if path else r'\{}'.format(subkey.name)
            else:
                subkey_path = f'\\{subkey.name}'

            # Leaf Index records do not contain subkeys
            if isinstance(subkey, LIRecord):
                continue

            #print(("\t"*depth)+str(subkey.subkey_count))
            if subkey.subkey_count:
                yield from recurse_subkeys(self,subkey.subkey_count,depth+1,nk_record=subkey,
                                                path=subkey_path,
                                                as_json=as_json,
                                                is_init=False)
            values = []
            if subkey.values_count:
                values = []
                '''
                try:
                    if as_json:
                        values = [attr.asdict(x) for x in subkey.iter_values(as_json=as_json)]
                    else:
                        values = list(subkey.iter_values(as_json=as_json))
                except RegistryParsingException as ex:
                    logger.exception(f'Failed to parse hive value at path: {path}')
                    values = []
                #'''
            ts = convert_wintime(subkey.header.last_modified)
            yield Subkey(subkey_name=subkey.name, path=subkey_path,
                            timestamp=ts.isoformat() if as_json else ts, values=values,
                            values_count=len(values),
                            actual_path=f'{self.partial_hive_path}{subkey_path}' if self.partial_hive_path else None)

    if is_init:
        # Get the values of the subkey
        values = []
        if nk_record.values_count:
            try:
                if as_json:
                    values = [attr.asdict(x) for x in nk_record.iter_values(as_json=as_json)]
                else:
                    values = list(nk_record.iter_values(as_json=as_json))
            except RegistryParsingException as ex:
                logger.exception(f'Failed to parse hive value at path: {path}')
                values = []

        ts = convert_wintime(nk_record.header.last_modified)
        subkey_path = path or '\\'
        yield Subkey(subkey_name=nk_record.name, path=subkey_path,
                        timestamp=ts.isoformat() if as_json else ts, values=values, values_count=len(values),
                        actual_path=f'{self.partial_hive_path}\\{subkey_path}' if self.partial_hive_path else None)

'''print("About to load")
reg = RegistryHive('./SOFTWARE.dat')
print("Loaded")'''

'''for subkey in recurse_subkeys(reg):
    #print("Got Key")
    subkey_path = subkey.path
    ts = subkey.timestamp
print("Completed")'''