int main(void) {  
    
    int f1 = open("demo.txt", "r+");
    double arg = f1.read;
    float sine = sin(arg);
    float cosine = cos(arg);
    if(tan(arg)==sine/cosine && sqrt(sine*sine + cosine*cosine) == 1){
        output("correct formula");
    }
    else{
        output("error");
    }
}    