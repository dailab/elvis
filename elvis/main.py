
import distribution

if __name__ == "__main__":
    dist = distribution.InterpolatedDistribution.linear([[0, 5], [1, 10], [2, 20]], None)
    print(dist[-5])
    print(dist[0])
    print(dist[0.5])
    print(dist[0.8])
    print(dist[1])
    print(dist[1.3])
    print(dist[70])

    norm = distribution.NormalDistribution(0, 1)
    print(norm[0])
    print(norm[.5])
