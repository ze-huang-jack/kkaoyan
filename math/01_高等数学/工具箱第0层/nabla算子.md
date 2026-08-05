
$$\nabla = \left( \frac{\partial}{\partial x}, \frac{\partial}{\partial y}, \frac{\partial}{\partial z} \right)$$

- **梯度 ($\nabla f$)**：$\nabla$ 直接作用于**标量** $f$ —— 结果是一个**向量**，表示变化最快的方向。
    
- **散度 ($\nabla \cdot \mathbf{F}$)**：$\nabla$ 与向量 $\mathbf{F}$ 进行**点乘** —— 结果是一个**标量**，表示某点发散或汇聚的程度。
    
- **旋度 ($\nabla \times \mathbf{F}$)**：$\nabla$ 与向量 $\mathbf{F}$ 进行**叉乘** —— 结果是一个**向量**，表示流体在某点旋转的剧烈程度和轴向



设：
标量函数：$f(x,y,z)$
向量场：$\mathbf{F}=(P,Q,R)$

$$
\nabla f=
\left(
\frac{\partial f}{\partial x},
\frac{\partial f}{\partial y},
\frac{\partial f}{\partial z}
\right)
$$

$$
\nabla\cdot\mathbf{F}
=
\frac{\partial P}{\partial x}
+
\frac{\partial Q}{\partial y}
+
\frac{\partial R}{\partial z}
$$

$$
\nabla\times\mathbf{F}
=
\left(
\frac{\partial R}{\partial y}-\frac{\partial Q}{\partial z},
\;
\frac{\partial P}{\partial z}-\frac{\partial R}{\partial x},
\;
\frac{\partial Q}{\partial x}-\frac{\partial P}{\partial y}
\right)
$$


