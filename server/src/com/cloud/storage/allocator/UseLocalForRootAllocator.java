// Copyright 2012 Citrix Systems, Inc. Licensed under the
// Apache License, Version 2.0 (the "License"); you may not use this
// file except in compliance with the License.  Citrix Systems, Inc.
// reserves all rights not expressly granted by the License.
// You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
// 
// Automatically generated by addcopyright.py at 04/03/2012
package com.cloud.storage.allocator;

import java.util.List;
import java.util.Map;

import javax.ejb.Local;
import javax.naming.ConfigurationException;

import com.cloud.configuration.Config;
import com.cloud.configuration.dao.ConfigurationDao;
import com.cloud.deploy.DeploymentPlan;
import com.cloud.deploy.DeploymentPlanner.ExcludeList;
import com.cloud.host.Host;
import com.cloud.storage.StoragePool;
import com.cloud.storage.Volume.Type;
import com.cloud.utils.component.ComponentLocator;
import com.cloud.vm.DiskProfile;
import com.cloud.vm.VirtualMachine;
import com.cloud.vm.VirtualMachineProfile;

@Local(value=StoragePoolAllocator.class)
public class UseLocalForRootAllocator extends LocalStoragePoolAllocator implements StoragePoolAllocator {
    boolean _useLocalStorage;

    @Override
    public List<StoragePool> allocateToPool(DiskProfile dskCh, VirtualMachineProfile<? extends VirtualMachine> vmProfile, DeploymentPlan plan, ExcludeList avoid, int returnUpTo) {
        if (!_useLocalStorage) {
            return null;
        }
        
        return super.allocateToPool(dskCh, vmProfile, plan, avoid, returnUpTo);
    }

    @Override
    public String chooseStorageIp(VirtualMachine vm, Host host, Host storage) {
        return null;
    }
    
    @Override
    public boolean configure(String name, Map<String, Object> params) throws ConfigurationException {
        super.configure(name, params);
        
        ComponentLocator locator = ComponentLocator.getCurrentLocator();
        ConfigurationDao configDao = locator.getDao(ConfigurationDao.class);
        Map<String, String> dbParams = configDao.getConfiguration(params);
        
        _useLocalStorage = Boolean.parseBoolean(dbParams.get(Config.UseLocalStorage.toString()));
        
        return true;
    }
    
    @Override
    protected boolean localStorageAllocationNeeded(DiskProfile dskCh) {
        if (dskCh.getType() == Type.ROOT) {
            return true;
        } else if (dskCh.getType() == Type.DATADISK) {
            return false;
        } else {
            return super.localStorageAllocationNeeded(dskCh);
        }
    }
    
    protected UseLocalForRootAllocator() {
    }
}
