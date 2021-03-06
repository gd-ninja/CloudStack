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
package com.cloud.agent.api.routing;

import java.util.ArrayList;
import java.util.List;

import com.cloud.agent.api.LogLevel;
import com.cloud.agent.api.LogLevel.Log4jLevel;

public class VmDataCommand extends NetworkElementCommand {
    
	String vmIpAddress;
	String vmName;
	@LogLevel(Log4jLevel.Trace)
	List<String[]> vmData;
	
    protected VmDataCommand() {
    }
    
    @Override
    public boolean executeInSequence() {
        return true;
    }
    
    public VmDataCommand(String vmIpAddress) {
    	this(vmIpAddress, null);
    }
    
    public String getVmName() {
        return vmName;
    }

    public VmDataCommand(String vmIpAddress, String vmName) {
        this.vmName = vmName;
        this.vmIpAddress = vmIpAddress;
        this.vmData = new ArrayList<String[]>();
    }
    
	
	public String getVmIpAddress() {
		return vmIpAddress;
	}
	
	public List<String[]> getVmData() {
		return vmData;
	}
	
	public void addVmData(String folder, String file, String contents) {
		vmData.add(new String[]{folder, file, contents});
	}
	
}
