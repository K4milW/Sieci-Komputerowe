import math
import sys

def ip_to_int(ip_str):
    octets = ip_str.split('.')
    return (int(octets[0]) << 24) + (int(octets[1]) << 16) + (int(octets[2]) << 8) + int(octets[3])

def int_to_ip(ip_int):
    return f"{(ip_int >> 24) & 255}.{(ip_int >> 16) & 255}.{(ip_int >> 8) & 255}.{ip_int & 255}"

def get_base_network():
    ip_input = input("Podaj adres sieci bazowej (np. 192.168.240.0/23) [domyślnie 192.168.240.0/23]: ").strip()
    if not ip_input:
        ip_input = "192.168.240.0/23"
    
    parts = ip_input.split('/')
    if len(parts) != 2:
        print("Nieprawidłowy format. Oczekiwano a.b.c.d/maska")
        sys.exit(1)
        
    ip_str = parts[0]
    mask = int(parts[1])
    
    base_ip_int = ip_to_int(ip_str)
    network_int = (base_ip_int >> (32 - mask)) << (32 - mask)
    
    return network_int, mask

def get_subnets():
    print("\nPodaj nazwy działów i ilość potrzebnych urządzeń (hostów).")
    print("Aby zakończyć wprowadzanie, wciśnij Enter bez wpisywania nazwy podsieci.")
    
    subnets = []
    
    while True:
        name = input("Nazwa podsieci (działu) [zostaw puste aby zakończyć/użyć domyślnego przypadku]: ").strip()
        if not name:
            if len(subnets) == 0:
                print("Używam danych z zadania (IT: 50, HR: 12, Księgowość: 10, Goście: 100).")
                subnets = [
                    ("IT", 50),
                    ("HR", 12),
                    ("Księgowość", 10),
                    ("Goście", 100)
                ]
            break
            
        try:
            val = input(f"Ilość urządzeń dla '{name}': ").strip()
            devices = int(val)
            subnets.append((name, devices))
        except ValueError:
            print("Nieprawidłowa wartość. Podaj liczbę całkowitą.")
            
    return subnets

class Node:
    def __init__(self, ip, mask):
        self.ip = ip
        self.mask = mask
        self.left = None
        self.right = None
        self.allocated_to = None

def build_allocator_tree(node, reqs_queue):
    if not reqs_queue:
        return
        
    largest = reqs_queue[0]
    req_mask = largest['mask']
    
    if node.mask == req_mask:
        node.allocated_to = reqs_queue.pop(0)
        return
    elif node.mask < req_mask: 
        child_mask = node.mask + 1
        child_size = 2 ** (32 - child_mask)
        node.left = Node(node.ip, child_mask)
        node.right = Node(node.ip + child_size, child_mask)
        
        build_allocator_tree(node.left, reqs_queue)
        if reqs_queue:
            build_allocator_tree(node.right, reqs_queue)

def print_tree(node, prefix="", is_last=True):
    if node is None:
        return
        
    marker = "└── " if is_last else "├── "
    next_prefix = prefix + ("    " if is_last else "│   ")
    
    size = 2 ** (32 - node.mask)
    if node.allocated_to:
        alloc = node.allocated_to
        print(f"{prefix}{marker}{int_to_ip(node.ip)}/{node.mask} ({size} adresów) -> [UŻYWANA] {alloc['name']} (wymagane z narzutem: {alloc['over_prov']})")
    elif node.left is None and node.right is None:
        print(f"{prefix}{marker}{int_to_ip(node.ip)}/{node.mask} ({size} adresów) -> [NIEUŻYWANA / REZERWA]")
    else:
        print(f"{prefix}{marker}{int_to_ip(node.ip)}/{node.mask} ({size} adresów) -> Podział na pół:")
        print_tree(node.left, next_prefix, is_last=False)
        print_tree(node.right, next_prefix, is_last=True)

def collect_leaves(node, leaves):
    if node is None:
        return
    if node.left is None and node.right is None:
        leaves.append(node)
    else:
        collect_leaves(node.left, leaves)
        collect_leaves(node.right, leaves)

def main():
    print("=== Kalkulator Podsieci (względem zapotrzebowania hostów) ===")
    base_ip_int, base_mask = get_base_network()
    subnets = get_subnets()
    
    reqs = []
    for name, devices in subnets:
        over_prov = math.ceil(devices * 1.5) + 1
        total_needed = over_prov + 2 
        power = math.ceil(math.log2(total_needed))
        allocated_addresses = 2 ** power
        mask = 32 - power
        
        reqs.append({
            'name': name,
            'devices': devices,
            'over_prov': over_prov,
            'allocated_addresses': allocated_addresses,
            'mask': mask,
            'usable': allocated_addresses - 2
        })
        
    reqs.sort(key=lambda x: x['allocated_addresses'], reverse=True)
    
    reqs_queue = list(reqs) 
    
    total_requested_space = sum(r['allocated_addresses'] for r in reqs)
    total_base_space = 2 ** (32 - base_mask)
    
    if total_requested_space > total_base_space:
        print(f"\n[BŁĄD]: Suma żądanych przestrzeni adresowych ({total_requested_space}) "
              f"przekracza wielkość podsieci bazowej ({total_base_space}).")
        return
        
    root = Node(base_ip_int, base_mask)
    try:
        build_allocator_tree(root, reqs_queue)
    except Exception as e:
        print("\n[BŁĄD]: Wystąpił niespodziewany błąd przy alokacji. Możliwa zbyt wysoka fragmentacja.")
        return
        
    if reqs_queue:
        print(f"\n[BŁĄD]: Nie udało się przydzielić wszystkich sieci z powodu fragmentacji. "
              f"Pominięto: {[r['name'] for r in reqs_queue]}")
    
    print("\n" + "="*60)
    print(" SZCZEGÓŁOWA LISTA PODSIECI ")
    print("="*60)
    
    leaves = []
    collect_leaves(root, leaves)
    
    unused_addresses = 0
    
    for leaf in leaves:
        if leaf.allocated_to:
            r = leaf.allocated_to
            net_ip = leaf.ip
            broadcast = net_ip + r['allocated_addresses'] - 1
            first_host = net_ip + 1
            last_host = broadcast - 1
            
            nadwyzka_min = r['usable'] - r['devices']
            nadwyzka_over = r['usable'] - r['over_prov']
            
            print(f"Nazwa: {r['name']}")
            print(f"Adres podsieci:       {int_to_ip(net_ip)}/{r['mask']}")
            print(f"Pierwszy adres hosta: {int_to_ip(first_host)}")
            print(f"Ostatni adres hosta:  {int_to_ip(last_host)}")
            print(f"Adres broadcast:      {int_to_ip(broadcast)}")
            print(f"Ilość hostów:         {r['devices']} "
                  f"(Z over-provisioningiem wymagano {r['over_prov']}, przydzielono jako maskę /{r['mask']} dającą {r['usable']} użytecznych adresów)")
            print(f"Nadwyżki ilości hostów:")
            print(f" - względem minimalnej ilości wymaganych hostów ({r['devices']}): {nadwyzka_min}")
            print(f" - względem over-provisioningu ({r['over_prov']}):        {nadwyzka_over}")
            print("-" * 60)
        else:
            size = 2 ** (32 - leaf.mask)
            unused_addresses += size
            
    print("\n" + "="*60)
    print(" DRZEWKO PODZIAŁU PODSIECI ")
    print("="*60)
    print_tree(root)
    
    print(f"\nIlość adresów IP nieprzydzielonych do żadnej podsieci: {unused_addresses}")

if __name__ == '__main__':
    main()