#include <math.h>

typedef int ll;
typedef float flt;


ll func(ll aax,ll bbx); 

ll main(){ 
    
    flt k;
    ll x; 




    x=ceil(5);
    output("ceil of 5 is ");
    output(x);
    output("\n");

    x=ceil(5.5);
    output("ceil of 5.5 is ");
    output(x);
    output("\n");

    x=floor(5.5);
    output("ceil of 5.5 is ");
    output(x);
    output("\n");

    x=floor(5);
    output("ceil of 5 is ");
    output(x);
    output("\n");

    k=factorial(5);
    output("factorial of 5 is ");
    output(k);
    output("\n");

    k=absol(-5);
    output("absol of -5 is ");
    output(k);
    output("\n");

    k=pow(2,10);
    output("2 to the power 10 is ");
    output(k);
    output("\n");

    k=sine(3.142,10);
    output("sine of pi is ");
    output(k);
    output("\n");

    k=tane(0.7854);
    output("tan of pi/4 is ");
    output(k);
    output("\n");

    k=coss(3.142,10);
    output("cosine of pi is ");
    output(k);
    output("\n");

    k=exp(2,10);
    output("exp of 2 is ");
    output(k);
    output("\n");

    k=neg_exp(2,10);
    output("neg_exp of 2 is ");
    output(k);
    output("\n");
    
    return 0; 


} 
