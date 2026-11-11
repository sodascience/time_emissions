clear all

year=[2017:2020];

n = 49;


for i=1:size(year,2) 

path=['.\IOT_' char(string(year(i))) '_pxp.\IOT_' char(string(year(i))) '_pxp'];
cd(path)

X=importdata("x.txt");
X1=X.data;
X2=X.textdata;

Y=importdata("Y.txt");
Y1=Y.data;
Y2=Y.textdata;

A=importdata("A.txt");
A1=A.data;
A2=A.textdata;

path=['./impacts'];
cd(path)

F=importdata("F.txt");
F1=F.data;
F2=F.textdata;


E=F1(126,1:end)./X1';
E(isnan(E))=0;
E(isinf(E))=0;

I=eye(size(A1));

L=(I-A1)^-1;

M=E*L;

for j=31 % China -> n=31 

Final(:,i)=Y1(:,(j-1)*7+1);

Footprint=M*diag(Final(:,i));

end









Footprint_year(:,i)=Footprint;

cd ..
cd ..
cd ..
end

Footprint_year_1=zeros(200,4);
for i=1:49

    Footprint_year_1 = Footprint_year_1+ Footprint_year((i-1)*200+1:(i-1)*200+200,:);

end

Final_1=zeros(200,4);
for i=1:49

    Final_1 = Final_1+ Final((i-1)*200+1:(i-1)*200+200,:);

end



bridge = [];

bridge'*Final_1;



