int main()
{
	int k=1;
	int e = 1;
	bool fg, xg;
	
	k++;
	k+=1;
	k<<=1;
	k>>=1;
	k*=9;
	k/=3;
	k-=2;
	k--;
	k^=2;
	k=k^2;
	k=k*2;
	k=k/2;
	k=k%2;
	k=k<<3;
	k=k>>1;
	k%=3;
	k=k/4;
    k|=2;
    k&=2;

	k = (1|2);
    fg= (e>4) || (e<5) && (e&2);
    xg= e>=0 && e<=90;
    return 0;
}

