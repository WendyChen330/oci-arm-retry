import oci
import time
import datetime

# ╔══════════════════════════════════════════════════════╗
# ║  Target : VM.Standard.E2.1.Micro (x86)               ║
# ║  Spec   : 1 OCPU / 1 GB RAM / 50 GB disk (default)   ║
# ║  Arch   : x86 (easier to claim than ARM)             ║
# ║  Tier   : Oracle Always Free (max 2 per account)     ║
# ║  OS     : Canonical Ubuntu 24.04 (UBUNTU_VERSION)    ║
# ╚══════════════════════════════════════════════════════╝

# ─── Configuration ───────────────────────────────────────
COMPARTMENT_ID = (
    "ocid1.tenancy.oc1..aaaaaaaaaqij5zlnm3v5qprvdll3j7nc6o3dk4ykzerugzxe37ckajkpjxpa"  # Replace with your tenancy OCID
)
SSH_PUBLIC_KEY = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCxPqVeut2vbwt8VVAvHDnEN+q61jrIAGD9cQgW6kTeLCjjzm9UHt2Flf1KoohSu+0YFvSn8+t67r9T9wfdP14WBfZAg531CCyUNTbF5KmkaHgmxftWu3FgY00BTnGa4YEEXdAGn3X953HzFKJDpJVJyWFfWXJUOWdfivTKlO+62SBnlIdcanckwA6rzr9dXNSYlasoVnuk+ujANjhnxf4TpKcI4AQrAmRJQ83lXfI2yExBMX+Qx/JNSA2/2XFRfT7OMgddExibCRpSyammfatNLUIM5s+ab6aeO3aNvVWGok6/dpYaBPbvndERQs6p9FQr88C/VFeEwHCtvMT8c2WB ssh-key-2026-03-07"  # Replace with your SSH public key (.pub file content)
INSTANCE_NAME = "micro-server"  # Change for each new instance (e.g. "micro-server-2" for a second one)
UBUNTU_VERSION = "24.04"  # OS for the new instance: "24.04" (default), "26.04" or "22.04"
BOOT_VOLUME_SIZE_IN_GBS = 50
RETRY_INTERVAL = 90  # seconds
# ────────────────────────────────────────────────────────

# ─── OCI Authentication ──────────────────────────────────
# [Local] Create a config file at ~/.oci/config
#   See README.md for format; key_file should point to your API private key .pem
#
# [GitHub Actions] No config file needed
#   The workflow auto-creates it from GitHub Secrets — see README.md
# ────────────────────────────────────────────────────────
config = oci.config.from_file()


def get_availability_domain():
    identity = oci.identity.IdentityClient(config)
    ads = identity.list_availability_domains(COMPARTMENT_ID).data
    return ads[0].name


def get_ubuntu_x86_image():
    compute = oci.core.ComputeClient(config)
    images = compute.list_images(
        COMPARTMENT_ID,
        operating_system="Canonical Ubuntu",
        operating_system_version=UBUNTU_VERSION,
        shape="VM.Standard.E2.1.Micro",
        sort_by="TIMECREATED",
        sort_order="DESC",
    ).data
    if not images:
        raise Exception(f"Ubuntu {UBUNTU_VERSION} x86 image not found")
    return images[0].id


def create_vcn_and_subnet():
    network = oci.core.VirtualNetworkClient(config)
    # Read-only lookups retry temporary errors (timeouts, 429, 5xx) with the SDK's
    # default strategy, so a brief OCI hiccup at startup doesn't stop the script.
    # Wrong OCIDs or keys (401/404) are not retried and still fail immediately.
    retry = oci.retry.DEFAULT_RETRY_STRATEGY

    # Check if VCN already exists
    vcns = network.list_vcns(
        COMPARTMENT_ID, display_name="retry-vcn-micro", retry_strategy=retry
    ).data
    if vcns:
        vcn = vcns[0]
        print(f"Using existing VCN: {vcn.id}")
    else:
        vcn = network.create_vcn(
            oci.core.models.CreateVcnDetails(
                compartment_id=COMPARTMENT_ID,
                display_name="retry-vcn-micro",
                cidr_block="10.1.0.0/16",
            )
        ).data
        print(f"Created VCN: {vcn.id}")

        # Create Internet Gateway
        ig = network.create_internet_gateway(
            oci.core.models.CreateInternetGatewayDetails(
                compartment_id=COMPARTMENT_ID,
                vcn_id=vcn.id,
                display_name="retry-ig-micro",
                is_enabled=True,
            )
        ).data

        # Update route table to allow outbound traffic
        network.update_route_table(
            vcn.default_route_table_id,
            oci.core.models.UpdateRouteTableDetails(
                route_rules=[
                    oci.core.models.RouteRule(
                        destination="0.0.0.0/0",
                        network_entity_id=ig.id,
                    )
                ]
            ),
        )

        # Open inbound ports: SSH / HTTP / HTTPS (add more ports to this list if needed)
        security_lists = network.list_security_lists(
            COMPARTMENT_ID, vcn_id=vcn.id, retry_strategy=retry
        ).data
        if security_lists:
            existing_egress = security_lists[0].egress_security_rules
            new_ingress = []
            for port in [22, 80, 443]:
                new_ingress.append(
                    oci.core.models.IngressSecurityRule(
                        protocol="6",
                        source="0.0.0.0/0",
                        tcp_options=oci.core.models.TcpOptions(
                            destination_port_range=oci.core.models.PortRange(
                                min=port, max=port
                            )
                        ),
                    )
                )
            network.update_security_list(
                security_lists[0].id,
                oci.core.models.UpdateSecurityListDetails(
                    ingress_security_rules=new_ingress,
                    egress_security_rules=existing_egress,
                ),
            )

    # Check if subnet already exists
    subnets = network.list_subnets(
        COMPARTMENT_ID, vcn_id=vcn.id, display_name="retry-subnet-micro", retry_strategy=retry
    ).data
    if subnets:
        subnet = subnets[0]
        print(f"Using existing subnet: {subnet.id}")
    else:
        subnet = network.create_subnet(
            oci.core.models.CreateSubnetDetails(
                compartment_id=COMPARTMENT_ID,
                vcn_id=vcn.id,
                display_name="retry-subnet-micro",
                cidr_block="10.1.0.0/24",
                prohibit_public_ip_on_vnic=False,
            )
        ).data
        print(f"Created subnet: {subnet.id}")

    return subnet.id


def try_create_instance(subnet_id, ad_name, image_id):
    compute = oci.core.ComputeClient(config)
    instance = compute.launch_instance(
        oci.core.models.LaunchInstanceDetails(
            compartment_id=COMPARTMENT_ID,
            display_name=INSTANCE_NAME,
            availability_domain=ad_name,
            shape="VM.Standard.E2.1.Micro",
            source_details=oci.core.models.InstanceSourceViaImageDetails(
                image_id=image_id,
                boot_volume_size_in_gbs=BOOT_VOLUME_SIZE_IN_GBS,
            ),
            create_vnic_details=oci.core.models.CreateVnicDetails(
                subnet_id=subnet_id,
                assign_public_ip=True,
            ),
            metadata={"ssh_authorized_keys": SSH_PUBLIC_KEY},
        )
    ).data
    return instance


def main():
    print("Initializing network configuration...")
    subnet_id = create_vcn_and_subnet()

    print("Fetching availability domain...")
    ad_name = get_availability_domain()
    print(f"AD: {ad_name}")

    print(f"Fetching Ubuntu {UBUNTU_VERSION} x86 image...")
    image_id = get_ubuntu_x86_image()
    print(f"Image ID: {image_id}")

    attempt = 0
    while True:
        attempt += 1
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n[{now}] Attempt #{attempt} to create instance...")

        try:
            instance = try_create_instance(subnet_id, ad_name, image_id)
            print(f"\n✅ Success! Instance created")
            print(f"   ID: {instance.id}")
            print(f"   State: {instance.lifecycle_state}")
            print(f"   Check Oracle Cloud Console for the public IP")
            break
        except oci.exceptions.ServiceError as e:
            if "Out of host capacity" in str(e) or "capacity" in str(e).lower():
                print(f"❌ Out of capacity, retrying...")
            else:
                print(f"❌ API error: {e.message}, retrying...")
        except Exception as e:
            print(f"⚠️ Network timeout or other error, retrying... ({type(e).__name__})")

        time.sleep(RETRY_INTERVAL)


if __name__ == "__main__":
    main()
