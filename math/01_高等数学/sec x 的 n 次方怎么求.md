设
$$
I_{n}=\int \sec^nx\:dx
$$
比如
$$
I_{5}=\int \sec^5 x\:dx
$$
$$
I_{3}=\int \sec^3x\:dx
$$
$$
I_{2}=\int \sec^2x\:dx = \tan x
$$
这是唯一容易积分的sec
$$
I_{1}=\int \sec x\:dx = \ln \left|\sec x+\tan x\right|
$$
这个乘一个 "1":
$$
\frac{\sec x+\tan x}{\sec x+\tan x}
$$
因为发现:
$$
(\ln(\sec x+\tan x))'=\sec x
$$
$$
I_{0}=\int \sec^0x\:dx = \int 1 \: dx = x
$$


所有递推最终会降到 $I_{1}$ 和 $I_{0}$


$$
I_{n}=\int \sec^nx \: dx
$$
因为$sec^2 x$ 是唯一一个好求的积分,拆一个$sec^2 x$ :
$$
I_{n}=\int \sec^{n-2}x \sec^2 x \: dx
$$
利用分部积分:
设$u=\sec^{n-2}x$
$dv=\sec^2xdx$
du
v=
带回去

得到递推公式:

$$
I_{n}=\frac{\sec^{n-2}x\tan x}{n-1}+\frac{n-2}{n-1}I_{n-2}
$$

