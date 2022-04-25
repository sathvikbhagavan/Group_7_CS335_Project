float factorial(int a){
    float k,t;
    if(a==1){
        return 1;
    }
    t=a-1;
    k = factorial(t);
    return a*k;
}
float sine(float x1,int place1){

    float ans;
    int i;
    float val1;
    float val3;
    float val2;
    float mul=1;
    float sign;
    sign=-1;
    ans=x1;
    val1=1;
    val2=x1;
    for(i=3;i<=place1;i+=2){
        val2= val2*x1*x1;
        val1= factorial(i);
        val3=val2*sign/val1;
        ans = ans + val3;
        sign=-1*sign;
    }
    return ans;
}

float coss(float x2,int place2){

    float ans;
    int i;
    float val1;
    float val3;
    float val2;
    float mul=1;
    float sign;
    sign=-1;
    ans=1;
    val1=1;
    val2=1;
    for(i=2;i<=place2;i+=2){
        val2= val2*x2*x2;
        val1= factorial(i);
        val3=val2*sign/val1;
        ans = ans + val3;
        sign=-1*sign;
    }
    return ans;
}

float pow(float x3, int y3)
{
    float h;
    int i;
    h=1;
    for(i=0;i<y3;i++)
    {
        h=h*x3;
    }
    return h;
}

float exp(float x4,float place4)
{
    float ans;
    int i;
    float val1;
    float val3;
    float val2;
    float mul=1;
    ans=1;
    val1=1;
    val2=1;
    for(i=1;i<=place4;i+=1){
        val2= val2*x4;
        val1= factorial(i);
        val3=val2/val1;
        ans = ans + val3;
    }
    return ans;
}

float neg_exp(float x5,float place5)
{
    float ans;
    int i;
    float sign;
    float val1;
    float val3;
    float val2;
    float mul=1;
    ans=1;
    val1=1;
    val2=1;
    sign=-1;
    for(i=1;i<=place5;i+=1){
        val2= val2*x5;
        val1= factorial(i);
        val3=sign*val2/val1;
        ans = ans + val3;
        sign=-1*sign;
    }
    return ans;
}

float tane(float x41)
{
    float th;
    float t1;

    th=0;
    th=th+x41;

    t1=pow(x41,3);
    t1=t1/3;
    th=th+t1;

    t1=pow(x41,5);
    t1=t1*2/15;
    th=th+t1;

    t1=pow(x41,5);
    t1=t1*2/15;
    th=th+t1;

    t1=pow(x41,7);
    t1=t1*17/315;
    th=th+t1;

    t1=pow(x41,9);
    t1=t1*62/2835;
    th=th+t1;

    return th;

}

int floor(float f71)
{
    int k;
    k=f71;
    return k;
}

int ceil(float fa8)
{
    int k;
    float j;
    int u;
    k=fa8;
    j=k;
    u=k+1;
    if(j==fa8)
    {
        u=k;
    }
    else
    {
        u=k+1;
    }
    return u;
}

float absol(float x9){
    float g;
    if(x9<0)
    {
        g=-1*x9;
    }
    else{
        g=x9;
    }
    return g;
}



