import java.io.*;
import java.net.InetAddress;
import java.net.Socket;
import java.net.UnknownHostException;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.Arrays;
import java.util.Random;




public class DemoHandshake {

    public static void main(String[] args) {

        InetAddress[] addresses = null;

        try {
            addresses = InetAddress.getAllByName("seed.bitcoin.sipa.be");
        } catch (UnknownHostException e) {
            e.printStackTrace();
        }

        try {
            if (addresses != null) {
                System.out.println(addresses[1].getHostAddress());
                Socket socket = new Socket(addresses[1].getHostAddress(), 8333);
                OutputStream s = socket.getOutputStream();
                s.write(getVersion());
                s.flush();
                InputStream stream = socket.getInputStream();
                byte[] data = new byte[2048];
                int count = stream.read(data);
                System.out.println(count);
            }
        } catch (IOException e) {
            e.printStackTrace();
        }

    }


    private static byte[] getVersion(){
        ByteArrayOutputStream ba = new ByteArrayOutputStream();
        DataOutputStream d = new DataOutputStream(ba);
        var magic = hexStringToByteArray("F9BEB4D9");
        var command = ("version" + "\00"+ "\00"+ "\00"+ "\00"+ "\00").getBytes();
        var version = 70015;
        var services = 0;
        var time = System.currentTimeMillis() / 1000L;
        var addr = "127.0.0.1".getBytes();
        var port = 8333;
        var agent = 0;
        var height = 565780;
        byte[] b = new byte[8];
        new Random().nextBytes(b);
        try {
            d.writeInt(version);
            d.writeByte(services);
            d.writeInt((int) time);
            d.writeByte(services);
            d.write(addr);
            d.writeInt(port);
            d.writeByte(services);
            d.write(addr);
            d.writeInt(port);
            d.write(b);
            d.writeByte(agent);
            d.writeInt(height);
            d.writeBoolean(false);
        } catch (IOException e) {
            e.printStackTrace();
        }

            byte[] payload = ba.toByteArray();
            byte[] checksum = new byte[4];

            try {
                MessageDigest digest = MessageDigest.getInstance("SHA-256");
                byte[] hash = digest.digest(payload);
                hash = digest.digest(hash);
                checksum = Arrays.copyOfRange(hash, hash.length-4, hash.length);
            } catch (NoSuchAlgorithmException e) {
                e.printStackTrace();
            }

            ByteArrayOutputStream outputStream = new ByteArrayOutputStream();
            DataOutputStream x = new DataOutputStream(outputStream);
        try {
            x.write(magic);
            x.write(command);
            x.writeInt(payload.length);
            x.write(checksum);
            x.write(payload);
        } catch (IOException e) {
            e.printStackTrace();
        }


        return  outputStream.toByteArray();
    }

    private static byte[] hexStringToByteArray(String s) {
        int len = s.length();
        byte[] data = new byte[len / 2];
        for (int i = 0; i < len; i += 2) {
            data[i / 2] = (byte) ((Character.digit(s.charAt(i), 16) << 4)
                    + Character.digit(s.charAt(i+1), 16));
        }
        return data;
    }




}
