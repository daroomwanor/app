import yaml
import io
        
eventYaml = {
    'apiVersion': 'v1',
    'kind': 'Pod',
    'metadata':{
        'name': 'event-service'
    },
    'spec': {
        'restartPolicy': 'Never',
        'volumes': [
            {
                'name':'shared-data',
                'emptyDir': {}
            }
        ],
        'containers':[
            {
                'name':'ubuntu-container',
                'image': 'ubuntu',
                'resources': {
                    'limits':{
                        'memory':'1Gi',
                        'cpu':'1',
                    },
                    'requests':{
                        'memory':'1Gi',
                        'cpu':'0.5',
                    },                    
                },
                'ports': [
                    {
                        'containerPort':80,
                    }
                ],
                'volumeMounts': [
                    {
                        'name': 'shared-data',
                        'mountPath': '/var',
                    }
                ],
                'command': ['/bin/bash'],
                'args' : ["-c","while true; do curl http://ec2-54-89-164-120.compute-1.amazonaws.com; sleep 10;done"],
                
            }
        ]
    
    }

}
        
kube = {
    'apiVersion': 'apps/v1',
    'kind': 'Deployment',
    'metadata': {
        'name': 'event-service'
    },
    'spec':{
        'selector':{
            'matchLabels':{
                'app': 'nginx'
            }
            
        },
        'replicas':1,
        'template':{
            'metadata':{
                'labels': 'nginx',
                'app': 'nginx'
            },
            'spec':{
                'containers':[
                    {
                        'name': 'nginx',
                        'image': 'nginx',
                        'ports': [
                            {
                                'containerPort':80
                            }
                        ]
                    }
                ]
            },
            
        }
    },
    
}

def configs(kind,name,image,mem):
    eventYaml['kind'] = kind
    eventYaml['metadata']['name'] = name
    eventYaml['spec']['containers'][0]['name']= image+'-container'
    eventYaml['spec']['containers'][0]['image']= image
    eventYaml['spec']['containers'][0]['resources']['requests']['cpu']=mem
# Write YAML file
    with io.open('/app/services/deploy/kube.yaml', 'w', encoding='utf8') as outfile:
        yaml.dump(eventYaml, outfile, default_flow_style=False, allow_unicode=True)
# Read YAML file
    with open('/app/services/deploy/kube.yaml', 'r') as stream:
        data_loaded = yaml.safe_load(stream)
    
    print(eventYaml == data_loaded)
    print(eventYaml)