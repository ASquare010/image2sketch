import pulumi
import pulumi_kubernetes as k8s

# Application configuration
class AppConfig:
    provider = k8s.Provider("k8s-provider")
    namespace_name = pulumi.Output("default")  # Use default namespace or customize
    replicas = 1  # Number of replicas
    runtime_class_name = pulumi.Output("nvidia")  # Assuming NVIDIA runtime for GPU
    cluster_version = "1.0.0"

opts = AppConfig()

# Application details
app_name = 'img2skch'
app_labels = {'app': app_name}
image_name = "img2skch:latest"  # Your container image

# Kubernetes Deployment
app_deployment = k8s.apps.v1.Deployment(
    f"{app_name}-{opts.cluster_version}",
    k8s.apps.v1.DeploymentArgs(
        metadata=k8s.meta.v1.ObjectMetaArgs(
            name=app_name,
            labels=app_labels,
            namespace=opts.namespace_name,
        ),
        spec=k8s.apps.v1.DeploymentSpecArgs(
            replicas=opts.replicas,
            selector=k8s.meta.v1.LabelSelectorArgs(match_labels=app_labels),
            template=k8s.core.v1.PodTemplateSpecArgs(
                metadata=k8s.meta.v1.ObjectMetaArgs(labels=app_labels),
                spec=k8s.core.v1.PodSpecArgs(
                    runtime_class_name=opts.runtime_class_name,  # Use NVIDIA runtime
                    containers=[
                        k8s.core.v1.ContainerArgs(
                            name=app_name,
                            image=image_name,
                            ports=[k8s.core.v1.ContainerPortArgs(container_port=5000)],  # Flask app runs on 5000
                            resources=k8s.core.v1.ResourceRequirementsArgs(
                                limits={
                                    "nvidia.com/gpu": "1",  # Request 1 GPU
                                },
                            ),
                            env=[
                                k8s.core.v1.EnvVarArgs(name="FLASK_ENV", value="production"),
                            ],
                            volume_mounts=[
                                k8s.core.v1.VolumeMountArgs(
                                    name="result-storage",
                                    mount_path="/app/results",  # Your results folder
                                ),
                            ],
                        ),
                    ],
                    volumes=[
                        k8s.core.v1.VolumeArgs(
                            name="result-storage",
                            empty_dir={},  # Ephemeral storage for processing
                        ),
                    ],
                ),
            ),
        ),
    ),
    opts=pulumi.ResourceOptions(provider=opts.provider),
)

# Kubernetes Service for exposing the app
app_service = k8s.core.v1.Service(
    f"{app_name}-service",
    k8s.core.v1.ServiceArgs(
        metadata=k8s.meta.v1.ObjectMetaArgs(
            name=f"{app_name}-service",
            namespace=opts.namespace_name,
        ),
        spec=k8s.core.v1.ServiceSpecArgs(
            selector=app_labels,
            ports=[k8s.core.v1.ServicePortArgs(port=5000, target_port=5000)],
            type="LoadBalancer",  # Expose the service externally
        ),
    ),
    opts=pulumi.ResourceOptions(provider=opts.provider),
)

# Export Deployment and Service details
pulumi.export("deployment_name", app_deployment.metadata["name"])
pulumi.export("service_name", app_service.metadata["name"])
