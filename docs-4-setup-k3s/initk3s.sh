kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/storage/storage-pvc.yaml
kubectl apply -f k8s/database/

# For each worker node:

# 1. From master node, copy the tar files to worker
scp music-service.tar user@WORKER1_IP:/home/user/
scp management-service.tar user@WORKER1_IP:/home/user/
scp storage-service.tar user@WORKER1_IP:/home/user/

# 2. SSH into the worker node
ssh user@WORKER1_IP

# 3. On the worker node, import the images
sudo k3s ctr images import music-service.tar
sudo k3s ctr images import management-service.tar
sudo k3s ctr images import storage-service.tar

# Deploy services in each node (on master node)
kubectl apply -f k8s/management/
kubectl apply -f k8s/storage/storage-deployment.yaml
kubectl apply -f k8s/music/

# deploy logging stack 
kubectl apply -f k8s/logging/

# Monitor the deployments
kubectl get pods -n music-app -w

#verify the deployment

# Check all resources
kubectl get all -n music-app

# Check pod distribution across nodes
kubectl get pods -n music-app -o wide



####################
# ROLL MANAGEMENT SERVICE

kubectl label nodes laptop-3k7ac59s kubernetes.io/role=worker
kubectl label nodes moonlight kubernetes.io/role=worker

# MASTER NODE
sudo kubectl apply -f k8s/namespace.yaml
sudo kubectl apply -f k8s/storage/storage-pvc.yaml
sudo kubectl apply -f k8s/database/

# WORKER NODE
sudo kubectl apply -f k8s/management/                       # OR kubectl apply -f management-deployment.tar
sudo kubectl apply -f k8s/storage/storage-deployment.yaml  # OR kubectl apply -f storage-deployment.tar
sudo kubectl apply -f k8s/music/                         # OR kubectl apply -f music-deployment.tar

# DELETE PODS
kubectl delete pod -n music-app elasticsearch-749657f9-t2mpp

# MONITOR LOG
sudo kubectl logs -n music-app music-service-7dd8b64599-rk958

sudo k3s ctr images list

# CONFIGMAP LOG

   kubectl create configmap logstash-config --from-file=logs-node/logstash/logstash.conf -n music-app
   kubectl create configmap metricbeat-config --from-file=logs-node/metricbeat/metricbeat.yml -n music-app


