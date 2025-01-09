import numpy as np

class Satellite:
    def __init__(self, a, e, i, omega, w, m, mu=398600.4418):
        self.a = a # Большая полуось в тыс.км
        self.e = e # Эксцентриситет 
        self.i = i # Наклонение орбиты
        self.omega = omega # Долгота восходящего узла
        self.w = w # Аргумент перицентра 
        self.m = m # Средняя аномалия
        self.mu = mu # Гравитационный параметр в км^3/с^2

    def mean_motion(self):
        return np.sqrt(self.mu / (self.a * 1000) **3)

    def mean_anomaly(self, t, t0):
        n = self.mean_motion()
        return self.m + n * (t - t0)

    def eccentric_anomaly(self, M):
        E = M
        for _ in range(10):  # Метод Ньютона для решения уравнения Кеплера
            E_next = E + (M - E + self.e * np.sin(E)) / (1 - self.e * np.cos(E))
            if abs(E_next - E) < 1e-8:
                break
            E = E_next
        return E

    def true_anomaly(self, E):
        #return 2 * np.arctan(np.sqrt((1 + self.e) / (1 - self.e)) * np.tan(E / 2))
        #return 2 * np.arctan2(np.sqrt(1 - self.e), np.sqrt(1 + self.e) * np.tan(E / 2))
        #return 2 * np.arctan2(np.sqrt(1 + self.e) * np.sin(E /2), np.sqrt(1 - self.e) * np.cos(E / 2))
        return 2 * np.arctan2(np.sqrt(1 - self.e) * np.cos(E /2), np.sqrt(1 + self.e) * np.sin(E / 2))

    #def radius(self, nu):
    #    return self.a * (1 - self.e**2) / (1 + self.e * np.cos(nu))

    def radius(self, E):
        return self.a * (1 - self.e * np.cos(E))

    def position(self, t, t0):
        M = self.mean_anomaly(t, t0)
        E = self.eccentric_anomaly(M)
        nu = self.true_anomaly(E)
        #r = self.radius(nu)
        r = self.radius(E)

        x_orb = r * np.cos(nu)
        y_orb = r * np.sin(nu)

        # Вычисление координат в экваториальной плоскости
        x_eq = x_orb * (np.cos(self.omega) * np.cos(self.w) - np.sin(self.omega) * np.sin(self.w) * np.cos(self.i)) - y_orb * (np.cos(self.omega) * np.sin(self.w) + np.sin(self.omega) * np.cos(self.w) * np.cos(self.i))
        y_eq = x_orb * (np.sin(self.omega) * np.cos(self.w) + np.cos(self.omega) * np.sin(self.w) * np.cos(self.i)) + y_orb * (-np.sin(self.omega) * np.sin(self.w) + np.cos(self.omega) * np.cos(self.w) * np.cos(self.i))
        z_eq = x_orb * np.sin(self.i) * np.sin(self.w) + y_orb * np.sin(self.i) * np.cos(self.w)

        return x_eq, y_eq, z_eq
    
    def orbit(self, n):
        rad = np.linspace(0, 2 * np.pi, n + 1)
        orbit = []
        for M in rad:
            E = self.eccentric_anomaly(M)
            nu = self.true_anomaly(E)
            # r = self.radius(nu)
            r = self.radius(E)

            x_orb = r * np.cos(nu)
            y_orb = r * np.sin(nu)

            # Вычисление координат в экваториальной плоскости
            x_eq = x_orb * (np.cos(self.omega) * np.cos(self.w) - np.sin(self.omega) * np.sin(self.w) * np.cos(self.i)) - y_orb * (np.cos(self.omega) * np.sin(self.w) + np.sin(self.omega) * np.cos(self.w) * np.cos(self.i))
            y_eq = x_orb * (np.sin(self.omega) * np.cos(self.w) + np.cos(self.omega) * np.sin(self.w) * np.cos(self.i)) + y_orb * (-np.sin(self.omega) * np.sin(self.w) + np.cos(self.omega) * np.cos(self.w) * np.cos(self.i))
            z_eq = x_orb * np.sin(self.i) * np.sin(self.w) + y_orb * np.sin(self.i) * np.cos(self.w)
            orbit.append((x_eq, y_eq, z_eq))
        return orbit


if __name__ == '__main__':
    # Пример использования
    satellite = Satellite(a=20, e=0.1, i=np.radians(30), omega=np.radians(45), w=np.radians(60), m=np.radians(90))
    t0 = 0
    t = 3600  # Время в секундах

    x, y, z = satellite.position(t0, t0)
    print(f"Координаты спутника в момент времени t0: x={x}, y={y}, z={z}")
    x, y, z = satellite.position(t, t0)
    print(f"Координаты спутника в момент времени t={t} секунд: x={x}, y={y}, z={z}")