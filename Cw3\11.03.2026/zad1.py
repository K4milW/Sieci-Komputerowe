def ip_cal():
    ip = input("Podaj adres IP razem z maską: ")
    maskk = ip.split("/")
    mask = int(maskk[1])
    ip_octets = maskk[0].split(".")
    ip = [int(i) for i in ip_octets]
    mask_bin = "1" * mask + "0" * (32 - mask)
    mask_bin = [mask_bin[i:i + 8] for i in range(0, len(mask_bin), 8)]
    mask_bin = [int(i, 2) for i in mask_bin]
    network = [ip[i] & mask_bin[i] for i in range(4)]
    broadcast = [network[i] | (mask_bin[i] ^ 255) for i in range(4)]
    print("Adres sieci: " + ".".join(str(i) for i in network))
    print("Adres rozgłoszeniowy: " + ".".join(str(i) for i in broadcast))
    print("Liczba hostów: " + str(2 ** (32 - mask) - 2))
    print("Pierwszy host: " + ".".join(str(i) for i in network[:3] + [network[3] + 1]))
    print("Ostatni host: " + ".".join(str(i) for i in broadcast[:3] + [broadcast[3] - 1]))
    print("Maska: " + ".".join(str(i) for i in mask_bin))
ip_cal()