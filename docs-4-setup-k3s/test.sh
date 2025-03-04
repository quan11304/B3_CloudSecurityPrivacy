kubectl run test-pod --image=busybox -n music-app --restart=Never -- /bin/sh -c sleep 3600
kubectl exec -it test-pod -n music-app -- /bin/sh
