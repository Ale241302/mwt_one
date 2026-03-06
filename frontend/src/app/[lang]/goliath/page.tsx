import InsideProduct from '@/components/InsideProduct';

export default function GoliathPage() {
    return (
        <InsideProduct
            productName="Goliath"
            primaryColor="#013A57"
            accentColor="#A8D8EA"
            techs={['LeapCore', 'ArchSystem', 'PORON_XRD', 'ThinBoom', 'NanoSpread']}
            seal="American Technology Inside"
            archProfiles={null}
        />
    );
}
