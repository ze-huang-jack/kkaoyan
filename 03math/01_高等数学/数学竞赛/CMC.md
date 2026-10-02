
# 一、题目

## (一)
![[Pasted image 20260924160322.png]]


设平面过原点与点 $(6,-3,2)$，且与平面 $4x-y+2z-8=0$ 垂直，则此平面方程为$\underline{\hspace{3cm}}.$


这个题目应该来说不难，我们要求的平面与另一个已知平面垂直，说明待求平面一定与已知平面的法向量平行，这一定是一个有用的条件

我想设待求平面方程为：$Ax+By+Cz+D=0$
带入原点求得D=0
带入点(6，-3，2)，得 $6A-3B+2C=0$
已知平面的法向量是$(4,-1,2)$
因为我们待求平面平行于(4,-1,2)，得：
$A:B:C=4:-1:2$
但是后面改怎么求呢，卡住了这里😖

，，，

问过chatgpt后，我发现我真是蠢啊，这里关键是用

两个平面垂直 iff 它们的法向量一定也垂直 ，也就是说$n_{1} \cdot n_{2} = 0$

利用这个来列方程啊

## (二)
![[Pasted image 20260924161652.png]]



(4) 设函数 $f(u,v)$ 具有一阶连续偏导数，$f(2,0)=3,\ f'_u(2,0)=5$，又设 $z=z(x,y)$ 是由方程 $xz=f(2x-y,xyz)$ 确定的隐函数，则 $\left.\dfrac{\partial z}{\partial x}\right|_{\substack{x=1\\y=0}}=\underline{\hspace{2cm}}.$


这个题目是多元微分学问题，这个题我想主要的突破点在于这个条件：
$z=z(x,y)$ 是由方程 $xz=f(2x-y,xyz)$ 确定的隐函数
所以只要我知道怎么求出z，后面的就好说了，但问题是我不知怎么求确定这个隐函数啊
一个三元函数的方程确定一个二元隐函数啊，该怎么求呢

这里我想要对方程$xz=f(2x-y,xyz)$ 两边同时对x求偏导，
令u=2x-y
v=xyz
z=f(x,y)

x->u->f
y->u->f
x->v->f
y->v->f
z=f(x,y)->v->f

这样的话该怎么求呢，我很困惑我学到的这个方法了，就是我上面写的这些传导箭头，我觉得我被这个方法困住了

我好像知道了，又好像不知道，

md这里fv最后竟然消掉了，因为y=0，😲


$$
\frac{\partial^2z}{\partial x\partial y}=\frac{\partial z}{\partial x} \cdot \frac{\partial z}{\partial y}
$$



## (三)

![[Pasted image 20260929121839.png]]


设 $f(x)$ 在 $(-\infty,+\infty)$ 上连续，在 $x=0$ 处可导，且满足$f(x) = x^3 + x^2\lim_{x\to 0}\frac{f(x)}{x} - x\int_{0}^{1}f(x)\mathrm{d}x.$ 求函数 $f(x)$ 的表达式

### idea
把一个复杂整体看做未知常数
这里$\lim_{ x \to 0 } \frac{f(x)}{x}$和 $\int_{0}^1 f(x)dx$ 其实都是确凿无疑的常数，所以分别设为A和B，那么$f(x)=x^3+Ax^2-Bx$
接下来就是精彩的部分了
1. 将上式两边同时除以x，令x->0，这样可以得到A=-B
2. 将f(x)的表达式带入B里面积分计算
这样就可以得到A和B，f(x)的表达式就顺势得到了

### 过程
![[Pasted image 20260929124026.png|661]]



## (四) 伯努利方程的变体
![[Pasted image 20260929131035.png]]


求微分方程 $y'x \ln x \sin y + (1 - x\cos y)\cos y = 0$ 的通解。

### idea
![[Pasted image 20260929132926.png]]

直接令u = cos y 

### 变体
#### 变体例子1

求微分方程 $y'x \ln x \cos y - (1 - x\sin y)\sin y = 0$ 的通解。

Ans: $\frac{1}{\sin y}=\frac{1}{\ln x}(x+C)$
只需要令$u=\sin y$，一切就迎刃而解了

![[Pasted image 20260929134359.png]]


积分因子公式法求解一阶线性微分方程
![[Pasted image 20260929134600.png|479]]

## (五) second order mixed partial derivative

![[Pasted image 20260929214518.png]]


![[Pasted image 20260929214525.png|498]]


### 变体
#### 变体例子 1
![[Pasted image 20260929215830.png]]
注：先对 x  求偏导，再对  y  求偏导

![[Pasted image 20260929220004.png]]
