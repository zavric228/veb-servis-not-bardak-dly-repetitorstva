q=1
w=0
while True:
    for i in range(4525000):
        q-=1
        q+=1
    w+=1
    e,r,t=str(w//3600),str(w//60),str(w%60)
    print((len(e)==1)*'0'+e+':'+(len(r)==1)*'0'+r+':'+(len(t)==1)*'0'+t)