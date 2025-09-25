25 sept ini lagi bikin ulang.

# perkara interface package
barusan gw colcon build salah tempat.
trus ada colcon build bahwa cmake g bisa nemuin srv yg gw minta dia bikin. katanya gaada di current directory package gw. ternyata, beneran gw salah ngasih nama wkwkwkwkwk blom diupdate ke nama interface yg baru dan kedobelan extension .srv nya wkwkwkwkk lol.

habis dibenerin, colcon buildnya berhasil koq.

# lagi bikin vision_perspective_transformer_node 

# lagi ngedit gui node yg bagian camera sidebar n perspective editor

# lagi launchfiles. 
ternyata ada pola berulang buat nambahin custom files n folder di package ros. pake yg os.path.join, trus diganti nama directory nya.
