// vm specs
param vmModel string = 'Standard_B2s'      // View available vm types with 'az vm list-skus -l centralus --output table
param osDiskSize int = 32                     // OS disk size in GB (allowable: 1 - 4,095 GB) https://azure.microsoft.com/en-gb/pricing/details/managed-disks/
param osDiskType string = 'Standard_LRS'       // choices are 'Premium_LRS' for premium SSD, 'StandardSSD_LRS' for standard SSD, 'Standard_LRS' for HDD platter 
param projectName string = 'b2s-flappy'             // If this parameter is not passed in at build it will default to this value.
param ipConfig string = 'ipconfig1'
param resourceGroupName string = resourceGroup().name
param resourceGroupLocation string = resourceGroup().location

// login credentials to be passed as secure string parameters
@secure() 
param adminUsername string
@secure()
param adminPublicKey string

// Advanced 
var vmName_var = '${projectName}-vm'
var VnetName_var = '${projectName}-VNet'
var vnetAddressPrefixes = '10.1.0.0/16' //CIDR notation
var SubnetName = '${projectName}-subnet'
var SubnetAddressPrefixes = '10.1.0.0/24'
var networkInterfaceName_var = '${projectName}-nic'
var publicIPAddressNameVM_var = '${projectName}-ip'
var networkSecurityGroupName_var = '${projectName}-nsg'
var subnetRef = resourceId(resourceGroupName, 'Microsoft.Network/virtualNetworks/subnets', VnetName_var, SubnetName)
var vmPort80 = 'Allow'      //'Allow' or 'Deny' (HTTP)
var vmPort443 = 'Allow'     //'Allow' or 'Deny' (HTTPS)
var vmPort22 = 'Allow'      //'Allow' or 'Deny' (SSH)
var vmDiskName = '${projectName}-disk'

// Describe the resources
resource publicIPAddressNameVM 'Microsoft.Network/publicIPAddresses@2020-05-01' = {
  name: publicIPAddressNameVM_var
  location: resourceGroupLocation
  properties: {
    publicIPAllocationMethod: 'Static'
  }
  sku: {
    name: 'Standard'
  }
}

resource VnetName 'Microsoft.Network/virtualNetworks@2020-05-01' = {
  name: VnetName_var
  location: resourceGroupLocation
  properties: {
    addressSpace: {
      addressPrefixes: [
        vnetAddressPrefixes
      ]
    }
    dhcpOptions: {
      dnsServers: []
    }
    subnets: [
      {
        name: SubnetName
        properties: {
          addressPrefix: SubnetAddressPrefixes 
          delegations: []
          privateEndpointNetworkPolicies: 'Enabled'
          privateLinkServiceNetworkPolicies: 'Enabled'
        }
      }    

    ]
    virtualNetworkPeerings: []
    enableDdosProtection: false
  }
}

resource networkSecurityGroupName 'Microsoft.Network/networkSecurityGroups@2020-05-01' = {
  name: networkSecurityGroupName_var
  location: resourceGroupLocation
  properties: {
    securityRules: [
      {
        name: 'HTTPS'
        properties: {
          priority: 320
          access: vmPort443 
          direction: 'Inbound'
          destinationPortRange: '443'
          protocol: 'Tcp'
          sourceAddressPrefix: '*'
          sourcePortRange: '*'
          destinationAddressPrefix: '*'
        }
      }
      {
        name: 'HTTP'
        properties: {
          priority: 340
          access: vmPort80
          direction: 'Inbound'
          destinationPortRange: '80'
          protocol: 'Tcp'
          sourceAddressPrefix: '*'
          sourcePortRange: '*'
          destinationAddressPrefix: '*'
        }
      }
      {
        name: 'SSH'
        properties: {
          priority: 360
          access: vmPort22
          direction: 'Inbound'
          destinationPortRange: '22'
          protocol: 'Tcp'
          sourceAddressPrefix: '*'
          sourcePortRange: '*'
          destinationAddressPrefix: '*'
        }
      }      
    ]
  }
}

resource networkInterfaceName 'Microsoft.Network/networkInterfaces@2020-05-01' = {
  name: networkInterfaceName_var
  location: resourceGroupLocation
  properties: {
    ipConfigurations: [
      {
        name: ipConfig
        properties: {
          privateIPAllocationMethod: 'Dynamic'
          publicIPAddress: {
            id: publicIPAddressNameVM.id
          }
          subnet: {
            id: subnetRef
          }
        }
      }
    ]
    networkSecurityGroup: {
      id: networkSecurityGroupName.id
    }
  }
  dependsOn: [
    VnetName
  ]
}

resource vmName 'Microsoft.Compute/virtualMachines@2019-12-01' = {
  name: vmName_var
  location: resourceGroupLocation
  properties: {
    hardwareProfile: {
      vmSize: vmModel
    }
    osProfile: {
      computerName: vmName_var
      adminUsername: adminUsername
      linuxConfiguration: {
        disablePasswordAuthentication: true
        ssh: {
          publicKeys: [
            {
              path: '/home/${adminUsername}/.ssh/authorized_keys'
              keyData: adminPublicKey
            }
          ]
        }
      }
    }
    storageProfile: {
      imageReference: {
        publisher: 'Canonical'
        offer: 'UbuntuServer'
        sku: '18.04-LTS'
        version: 'latest'
      }
      osDisk: {
        name: vmDiskName
        createOption: 'FromImage'
        diskSizeGB: osDiskSize
        caching: 'ReadWrite'
        managedDisk: {
          storageAccountType: osDiskType
        }
      }  
    }
    networkProfile: {
      networkInterfaces: [
        {
          id: networkInterfaceName.id
        }
      ]
    }
  }
}

